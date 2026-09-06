# ADVANCE-IBVAP

**Intelligent Border Video Analytics Platform**

AI-Based Intelligent Video Analytics Platform for Border Surveillance using existing CCTV Infrastructure.

**Problem Statement ID:** 26187  
**Organization:** Ministry of Home Affairs  
**Department:** Sashastra Seema Bal (SSB)

---

## Quick Start

### 1. Clone
```bash
git clone https://github.com/Animesh2229/ADVANCE-IBVAP.git
cd ADVANCE-IBVAP
```

### 2. Environment Setup
```bash
cp .env.example .env
# Set SECRET_KEY, ADMIN_PASSWORD, EDGE_FERNET_KEY, EDGE_HMAC_SECRET
# Fernet key:
#   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

`EDGE_FERNET_KEY` and `EDGE_HMAC_SECRET` **must be identical** on Central and every Edge device. Edge will not start without them. Central rejects unsigned / undecryptable alerts.

When `ENVIRONMENT=production`, `SECRET_KEY` (>=32 chars) is **required** — Central will not start with a random key.

### 3. Download AI Models (first time)
```bash
cd scripts
python download_models.py
cd ..
```

### 4. Start Database + Central
```bash
docker-compose up -d
cd central
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python create_admin.py
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Dashboard
```bash
cd dashboard
npm install
npm run dev
```
Open the Vite URL. First admin login **forces a password change**. JWT is stored in an **httpOnly cookie** (not localStorage).

### 6. Edge
```bash
cd edge
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# export EDGE_FERNET_KEY and EDGE_HMAC_SECRET (same as Central)
python main_edge.py
```

### 7. Field App (Optional)
```bash
cd field-app
npm install
npx expo start
```

---

## Features (v1.2.1)

- Human & Vehicle Detection + Tracking (YOLOv11, graceful fallback if missing)
- Face detection **and embeddings sent to Central** (fusion + watchlist match)
- ANPR plates **sent to Central** (India / Nepal / Bhutan)
- Virtual Fence + Night Enhancement
- Real-time Alerts via WebSocket (+ polling fallback)
- HMAC + Fernet on `/api/v1/alerts/secure` (no anonymous inject)
- **Per-camera rate limiting** on secure ingest (optional Redis via `REDIS_URL`)
- Role-based Access Control, httpOnly JWT cookie
- Vehicle + Face watchlist
- Multi-camera Fusion (face + plate)
- C2 pull export **and** outbound webhook (`C2_WEBHOOK_URL`)
- Field Mobile App
- Offline alert queue
- Immutable hash-chain audit log
- CI with **real tests** (no `|| true`)

---

## Security Notes

- `EDGE_FERNET_KEY` + `EDGE_HMAC_SECRET` required. Central **decrypts** `encrypted_payload` and **ignores** plaintext sidecar fields.
- `/api/v1/alerts/secure` rejects missing/invalid HMAC (5-minute skew) and rate-limits per `camera_id`.
- JWT in httpOnly cookie; Bearer still accepted for Field App.
- First admin login must change password.
- Production mode hard-fails without `SECRET_KEY`.
- Never commit `.env`.

---

## Status & honesty note

This repository is a **working reference implementation** for Problem Statement 26187 (SSB / Police II).  
Security basics (HMAC+Fernet alerts, httpOnly JWT, forced password change, per-camera rate limits) are implemented and unit-tested.

**It is still a prototype-grade system** relative to a full production border deployment:

- Fusion / WebSocket state is **in-memory** (optional Redis only for rate limits when `REDIS_URL` is set).
- Face/ANPR accuracy depends on model choice, camera placement, and field calibration.
- Before live border use: independent security audit, load test at target BOP scale, and integration UAT with the actual C2 system.

Do **not** treat an un-audited clone as production-ready for operational border control.

---

## Tests
```bash
cd central && PYTHONPATH=. pytest tests/ -v
cd ../edge && PYTHONPATH=. pytest tests/ -v
```

## Documentation
- [Architecture](docs/ARCHITECTURE.md)
- [Deployment](docs/DEPLOYMENT.md)
- [C2 integration](docs/C2_INTEGRATION.md)
