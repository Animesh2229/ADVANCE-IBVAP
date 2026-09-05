from fastapi import FastAPI, Depends, HTTPException, status, Request, WebSocket, WebSocketDisconnect
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

from db.models import Base, User, Alert, VehicleWatchlist

try:
    from services.fusion import fusion_engine
except ImportError:
    fusion_engine = None

try:
    from api.websocket import manager as ws_manager
except ImportError:
    ws_manager = None

# ===================== CONFIG FROM ENV =====================
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY or len(SECRET_KEY) < 32:
    SECRET_KEY = secrets.token_urlsafe(48)
    print("[WARNING] SECRET_KEY not set or too short. Using temporary key. Set SECRET_KEY in environment for production!")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://ibvap:ibvap@localhost/ibvap")
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

app = FastAPI(title="IBVAP Central API", version="1.1.0", docs_url="/docs" if ENVIRONMENT == "development" else None)

# ===================== CORS (Restricted) =====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS else ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ===================== Simple In-Memory Rate Limiter =====================
login_attempts = defaultdict(list)

def check_rate_limit(ip: str, max_attempts: int = 5, time_window: int = 60):
    now = time.time()
    attempts = login_attempts[ip]
    login_attempts[ip] = [t for t in attempts if now - t < time_window]
    if len(login_attempts[ip]) >= max_attempts:
        return False
    login_attempts[ip].append(now)
    return True

# ===================== Security Headers Middleware =====================
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# ===================== Global Exception Handler =====================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "correlation_id": secrets.token_hex(8)}
    )

# ===================== Auth Helpers =====================
def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
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

def require_roles(allowed_roles: List[str]):
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

# ===================== Schemas =====================
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: str = "operator"

# ===================== Routes =====================
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/api/v1/auth/login", response_model=Token)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_ip, max_attempts=5, time_window=60):
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")

    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    user.last_login = datetime.utcnow()
    await db.commit()
    token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "role": user.role, "full_name": user.full_name}

@app.post("/api/v1/auth/register")
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db),
                   current_user: User = Depends(require_roles(["admin"]))):
    existing = await db.execute(select(User).where(User.username == user_in.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role
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
        "email": current_user.email
    }

@app.get("/api/v1/users")
async def list_users(current_user: User = Depends(require_roles(["admin"])), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active
        } for u in users
    ]

@app.get("/api/v1/alerts")
async def get_alerts(skip: int = 0, limit: int = 50,
                     current_user: User = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).order_by(Alert.timestamp.desc()).offset(skip).limit(min(limit, 100)))
    return result.scalars().all()

@app.post("/api/v1/alerts/secure")
async def receive_secure_alert(alert_data: dict, db: AsyncSession = Depends(get_db)):
    new_alert = Alert(
        camera_id=alert_data.get("camera_id"),
        alert_type=alert_data.get("alert_type") or alert_data.get("type"),
        confidence=alert_data.get("confidence", 0),
        bbox=alert_data.get("bbox"),
        priority=alert_data.get("priority", "LOW"),
        raw_data=alert_data,
        event_hash=str(alert_data.get("signature", ""))[:64]
    )
    db.add(new_alert)
    await db.commit()
    await db.refresh(new_alert)

    if ws_manager is not None:
        try:
            await ws_manager.broadcast({
                "type": "new_alert",
                "data": {
                    "id": new_alert.id,
                    "camera_id": new_alert.camera_id,
                    "alert_type": new_alert.alert_type,
                    "priority": new_alert.priority,
                    "confidence": new_alert.confidence,
                    "timestamp": new_alert.timestamp.isoformat() if new_alert.timestamp else None,
                    "status": new_alert.status
                }
            })
        except Exception:
            pass

    if fusion_engine is not None:
        try:
            fusion_engine.update(
                camera_id=alert_data.get("camera_id", "unknown"),
                local_track_id=alert_data.get("track_id", 0),
                label=alert_data.get("subtype") or alert_data.get("alert_type") or "unknown",
                embedding=alert_data.get("face_embedding"),
                plate=alert_data.get("plate")
            )
        except Exception:
            pass

    return {"status": "accepted", "alert_id": new_alert.id}

@app.post("/api/v1/alerts/{alert_id}/action")
async def alert_action(alert_id: int, data: dict,
                       current_user: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = data.get("action", "acknowledged")
    await db.commit()
    return {"msg": "Action recorded", "status": alert.status}

@app.get("/api/v1/watchlist")
async def get_watchlist(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VehicleWatchlist).order_by(VehicleWatchlist.created_at.desc()))
    return result.scalars().all()

@app.post("/api/v1/watchlist")
async def add_watchlist(data: dict, current_user: User = Depends(require_roles(["admin", "commander"])),
                        db: AsyncSession = Depends(get_db)):
    plate = data.get("plate_number", "").upper().replace(" ", "").replace("-", "")
    if not plate or len(plate) < 4:
        raise HTTPException(status_code=400, detail="Invalid plate number")
    existing = await db.execute(select(VehicleWatchlist).where(VehicleWatchlist.plate_number == plate))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Plate already exists")
    record = VehicleWatchlist(
        plate_number=plate,
        country=data.get("country", "IND"),
        vehicle_type=data.get("vehicle_type"),
        owner_name=data.get("owner_name"),
        status=data.get("status", "watch"),
        notes=data.get("notes"),
        created_by=current_user.username
    )
    db.add(record)
    await db.commit()
    return {"msg": "Added to watchlist", "plate": plate}

@app.get("/api/v1/fusion/active")
async def get_active_global_tracks(current_user: User = Depends(get_current_user)):
    if fusion_engine is None:
        return {}
    return fusion_engine.get_active_tracks()

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
        "version": "1.1.0",
        "websocket_clients": len(ws_manager.active_connections) if ws_manager else 0
    }

@app.get("/")
async def root():
    return {"message": "IBVAP Central API is running", "version": "1.1.0"}
