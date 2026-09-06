from fastapi import FastAPI, Depends, HTTPException, status, Request, WebSocket, WebSocketDisconnect, Cookie, Header, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional, List
from collections import defaultdict
import os
import time
import secrets

from db.models import Base, User, Alert, VehicleWatchlist, ImmutableEvent, FaceEmbedding

try:
    from services.chain import append_event
except ImportError:
    append_event = None

try:
    from services.fusion import fusion_engine
except ImportError:
    fusion_engine = None

try:
    from services.face_match import best_match
except ImportError:
    best_match = None

try:
    from services.edge_auth import load_secrets, unwrap_secure_body
except ImportError:
    load_secrets = None
    unwrap_secure_body = None

try:
    from api.websocket import manager as ws_manager
except ImportError:
    ws_manager = None

try:
    from services.rate_limit import alert_limiter
except ImportError:
    alert_limiter = None

try:
    from services.c2_webhook import push_alert_to_c2
except ImportError:
    push_alert_to_c2 = None

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY or len(SECRET_KEY) < 32:
    if ENVIRONMENT == "production":
        raise RuntimeError(
            "SECRET_KEY must be set to a value >= 32 characters when ENVIRONMENT=production. "
            "Refusing to start with a random key (sessions would invalidate on every restart)."
        )
    SECRET_KEY = secrets.token_urlsafe(48)
    print("[WARNING] SECRET_KEY not set or too short. Using temporary key (development only).")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://ibvap:ibvap@localhost/ibvap")
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

app = FastAPI(title="IBVAP Central API", version="1.2.1", docs_url="/docs" if ENVIRONMENT == "development" else None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-IBVAP-Signature", "X-IBVAP-Timestamp"],
)

_login_attempts = defaultdict(list)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: Optional[str] = None
    must_change_password: bool = False


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _set_auth_cookie(response: Response, token: str):
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=(ENVIRONMENT == "production"),
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    elif access_token:
        token = access_token
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_roles(roles: List[str]):
    async def checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return checker


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.post("/api/v1/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db), request: Request = None):
    client_ip = request.client.host if request and request.client else "unknown"
    now = time.time()
    _login_attempts[client_ip] = [t for t in _login_attempts[client_ip] if now - t < 60]
    if len(_login_attempts[client_ip]) >= 10:
        raise HTTPException(status_code=429, detail="Too many login attempts")

    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        _login_attempts[client_ip].append(now)
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    user.last_login = datetime.utcnow()
    await db.commit()
    token = create_access_token(data={"sub": user.username, "role": user.role})
    body = {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "full_name": user.full_name,
        "must_change_password": bool(getattr(user, "must_change_password", False)),
    }
    response = JSONResponse(content=body)
    _set_auth_cookie(response, token)
    return response


@app.post("/api/v1/auth/logout")
async def logout():
    response = JSONResponse(content={"msg": "logged out"})
    response.delete_cookie("access_token", path="/")
    return response


@app.post("/api/v1/auth/change-password")
async def change_password(data: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    current = data.get("current_password") or ""
    new = data.get("new_password") or ""
    if len(new) < 8:
        raise HTTPException(status_code=400, detail="new_password must be at least 8 characters")
    if not verify_password(current, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="current_password is incorrect")
    current_user.hashed_password = get_password_hash(new)
    current_user.must_change_password = False
    await db.commit()
    return {"msg": "password updated"}


@app.post("/api/v1/auth/register")
async def register(data: dict, current_user: User = Depends(require_roles(["admin"])), db: AsyncSession = Depends(get_db)):
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")
    result = await db.execute(select(User).where(User.username == username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")
    new_user = User(
        username=username,
        email=data.get("email", f"{username}@ibvap.local"),
        hashed_password=get_password_hash(password),
        full_name=data.get("full_name", username),
        role=data.get("role", "operator"),
        must_change_password=True,
    )
    db.add(new_user)
    await db.commit()
    return {"msg": "User created successfully"}


@app.get("/api/v1/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "email": current_user.email,
        "must_change_password": bool(getattr(current_user, "must_change_password", False)),
    }


@app.get("/api/v1/users")
async def list_users(current_user: User = Depends(require_roles(["admin"])), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [{"id": u.id, "username": u.username, "full_name": u.full_name, "email": u.email, "role": u.role, "is_active": u.is_active} for u in users]


def _bop_from_camera(camera_id: str) -> str:
    if not camera_id:
        return "UNKNOWN"
    if "-CAM" in camera_id:
        return camera_id.split("-CAM")[0]
    parts = camera_id.split("-")
    return "-".join(parts[:2]) if len(parts) >= 2 else camera_id


@app.get("/api/v1/alerts")
async def get_alerts(skip: int = 0, limit: int = 50, bop: Optional[str] = None,
                     current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(Alert).order_by(Alert.timestamp.desc())
    if bop:
        q = q.where(Alert.camera_id.startswith(bop))
    result = await db.execute(q.offset(skip).limit(min(limit, 100)))
    return result.scalars().all()


@app.get("/api/v1/bops")
async def list_bops(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert.camera_id).order_by(Alert.timestamp.desc()).limit(2000))
    cams = result.scalars().all()
    bops = sorted({_bop_from_camera(c) for c in cams if c})
    return {"total": len(bops), "bops": bops}


@app.post("/api/v1/alerts/secure")
async def receive_secure_alert(
    alert_data: dict,
    db: AsyncSession = Depends(get_db),
    x_ibvap_signature: Optional[str] = Header(None),
    x_ibvap_timestamp: Optional[str] = Header(None),
):
    """Edge ingest: HMAC + Fernet required. Plaintext fields in the body are ignored."""
    if load_secrets is None or unwrap_secure_body is None:
        raise HTTPException(status_code=503, detail="edge auth module missing")
    try:
        fkey, hkey = load_secrets()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    try:
        payload = unwrap_secure_body(
            alert_data,
            timestamp=x_ibvap_timestamp or alert_data.get("timestamp"),
            signature=x_ibvap_signature or alert_data.get("signature"),
            fernet_key=fkey,
            hmac_secret=hkey,
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    camera_id = payload.get("camera_id")
    alert_type = payload.get("type") or payload.get("alert_type")
    embedding = payload.get("embedding")
    plate = payload.get("plate")
    priority = payload.get("priority", "LOW")

    # Per-camera rate limit (protects Central if an edge key leaks)
    if alert_limiter is not None and camera_id:
        allowed, remaining = alert_limiter.allow(str(camera_id))
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded for camera {camera_id}. Retry later.",
                headers={"Retry-After": "60"},
            )

    # Live face watchlist match
    face_hit = None
    if alert_type == "FACE" and embedding and best_match is not None:
        rows = (await db.execute(select(FaceEmbedding).where(FaceEmbedding.is_watchlist == True))).scalars().all()
        gallery = [(r.id, r.person_name or "unknown", r.embedding or []) for r in rows]
        face_hit = best_match(embedding, gallery, threshold=0.45)
        if face_hit:
            priority = "HIGH"
            payload["watchlist_hit"] = face_hit

    new_alert = Alert(
        camera_id=camera_id,
        alert_type=alert_type,
        subtype=payload.get("subtype"),
        confidence=payload.get("confidence", 0),
        bbox=payload.get("bbox"),
        track_id=payload.get("track_id"),
        timestamp=datetime.utcnow(),
        status="new",
        priority=priority,
        raw_data={k: v for k, v in payload.items() if k != "embedding"},
    )
    db.add(new_alert)
    await db.commit()
    await db.refresh(new_alert)

    if append_event is not None:
        try:
            eh = await append_event(
                db,
                event_type=new_alert.alert_type or "ALERT",
                data={"alert_id": new_alert.id, "camera_id": new_alert.camera_id, "priority": new_alert.priority},
                source=new_alert.camera_id or "edge",
            )
            new_alert.event_hash = eh
            await db.commit()
        except Exception:
            pass

    if fusion_engine is not None:
        try:
            label = payload.get("subtype") or alert_type or "unknown"
            if alert_type == "FACE":
                label = "person"
            elif alert_type == "ANPR":
                label = "vehicle"
            fusion_engine.update(
                camera_id=camera_id or "unknown",
                local_track_id=payload.get("track_id") or 0,
                label=label,
                embedding=embedding,
                plate=plate,
            )
        except Exception:
            pass

    if ws_manager is not None:
        try:
            await ws_manager.broadcast({
                "type": "new_alert",
                "data": {
                    "id": new_alert.id,
                    "camera_id": new_alert.camera_id,
                    "alert_type": new_alert.alert_type,
                    "subtype": new_alert.subtype,
                    "confidence": new_alert.confidence,
                    "priority": new_alert.priority,
                    "status": new_alert.status,
                    "plate": plate,
                    "watchlist_hit": face_hit,
                    "timestamp": new_alert.timestamp.isoformat() if new_alert.timestamp else None,
                },
            })
        except Exception:
            pass

    # Optional outbound push to external C2 when C2_WEBHOOK_URL is set
    if push_alert_to_c2 is not None:
        try:
            await push_alert_to_c2(new_alert)
        except Exception:
            pass

    return {"msg": "Alert received", "id": new_alert.id, "watchlist_hit": face_hit}


@app.post("/api/v1/alerts/{alert_id}/action")
async def alert_action(alert_id: int, data: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = data.get("action", alert.status)
    await db.commit()
    return {"msg": "updated", "status": alert.status}


@app.get("/api/v1/watchlist")
async def get_watchlist(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VehicleWatchlist))
    return result.scalars().all()


@app.post("/api/v1/watchlist")
async def add_watchlist(data: dict, current_user: User = Depends(require_roles(["admin", "commander"])), db: AsyncSession = Depends(get_db)):
    item = VehicleWatchlist(
        plate_number=data.get("plate_number"),
        country=data.get("country", "IND"),
        vehicle_type=data.get("vehicle_type"),
        owner_name=data.get("owner_name"),
        status=data.get("status", "watch"),
        notes=data.get("notes"),
        created_by=current_user.username,
    )
    db.add(item)
    await db.commit()
    return {"msg": "added"}


@app.get("/api/v1/face-watchlist")
async def list_face_watchlist(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FaceEmbedding).where(FaceEmbedding.is_watchlist == True))
    rows = result.scalars().all()
    return [
        {"id": r.id, "person_name": r.person_name, "camera_id": r.camera_id, "timestamp": r.timestamp}
        for r in rows
    ]


@app.post("/api/v1/face-watchlist")
async def add_face_watchlist(
    data: dict,
    current_user: User = Depends(require_roles(["admin", "commander"])),
    db: AsyncSession = Depends(get_db),
):
    emb = data.get("embedding")
    if not emb or not data.get("person_name"):
        raise HTTPException(status_code=400, detail="person_name and embedding required")
    row = FaceEmbedding(
        person_name=data["person_name"],
        embedding=emb,
        camera_id=data.get("camera_id") or "enroll",
        is_watchlist=True,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"msg": "enrolled", "id": row.id}


@app.post("/api/v1/face-watchlist/match")
async def match_face(data: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if best_match is None:
        raise HTTPException(status_code=501, detail="matcher unavailable")
    query = data.get("embedding")
    if not query:
        raise HTTPException(status_code=400, detail="embedding required")
    threshold = float(data.get("threshold", 0.45))
    result = await db.execute(select(FaceEmbedding).where(FaceEmbedding.is_watchlist == True))
    rows = result.scalars().all()
    gallery = [(r.id, r.person_name or "unknown", r.embedding or []) for r in rows]
    hit = best_match(query, gallery, threshold=threshold)
    return {"match": hit is not None, "result": hit}


@app.get("/api/v1/fusion/active")
async def get_active_global_tracks(current_user: User = Depends(get_current_user)):
    if fusion_engine is None:
        return []
    return fusion_engine.get_active_tracks()


@app.post("/api/v1/c2/export")
async def c2_export(
    data: dict = None,
    current_user: User = Depends(require_roles(["admin", "commander"])),
    db: AsyncSession = Depends(get_db),
):
    data = data or {}
    limit = min(int(data.get("limit", 50)), 200)
    result = await db.execute(
        select(Alert).where(Alert.priority.in_(["HIGH", "MEDIUM"])).order_by(Alert.timestamp.desc()).limit(limit)
    )
    alerts = result.scalars().all()
    return {
        "system": "IBVAP",
        "organization": "SSB / Police II Division",
        "schema": "ibvap.c2.v1",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "events": [
            {
                "event_id": a.id,
                "camera_id": a.camera_id,
                "type": a.alert_type,
                "subtype": a.subtype,
                "priority": a.priority,
                "status": a.status,
                "confidence": a.confidence,
                "timestamp": a.timestamp.isoformat() if a.timestamp else None,
                "event_hash": a.event_hash,
            }
            for a in alerts
        ],
    }


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    if ws_manager is None:
        await websocket.close(code=1011)
        return
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception:
        await ws_manager.disconnect(websocket)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "IBVAP Central",
        "version": "1.2.1",
        "websocket_clients": len(ws_manager.active_connections) if ws_manager else 0,
        "c2_webhook_configured": bool(os.getenv("C2_WEBHOOK_URL", "").strip()),
        "redis_rate_limit": bool(os.getenv("REDIS_URL", "").strip()),
    }


@app.get("/")
async def root():
    return {"message": "IBVAP Central API is running", "version": "1.2.1"}
