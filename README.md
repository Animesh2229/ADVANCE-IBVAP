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
```

When `ENVIRONMENT=production`, `SECRET_KEY` (>=32 chars) is **required**.

### 3–7
See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for Central, Dashboard, Edge, Field App, Redis, VPN, and scale notes.

---

## Features (v1.3.0)

- Human & Vehicle Detection + Tracking (YOLOv11 + **SORT-style Kalman/IoU tracker**)
- Face detection and embeddings to Central (vectorized match + optional FAISS)
- ANPR plates to Central (India / Nepal / Bhutan)
- Virtual Fence + Night Enhancement
- Real-time Alerts via WebSocket (+ Redis pub/sub fanout when configured)
- HMAC + Fernet on `/api/v1/alerts/secure` + per-camera rate limiting
- Role-based Access Control, httpOnly JWT cookie, forced password change
- Vehicle + Face watchlist
- Multi-camera Fusion with optional `FUSION_STATE_PATH` persistence
- C2 pull export + outbound webhook
- Optional HIGH/MEDIUM alert snapshots from Edge
- Offline alert queue
- Immutable hash-chain audit log + `/api/v1/chain/verify`
- CI with real tests; `scripts/eval_metrics.py` micro-benchmarks

---

## Security Notes

- Shared `EDGE_FERNET_KEY` + `EDGE_HMAC_SECRET` required
- Production hard-fails without `SECRET_KEY`
- Never commit `.env`

---

## Status & honesty note

Working reference implementation for PS 26187. Security basics and unit tests are in place.

Still prototype-grade vs full operational border deploy:

- Fusion can snapshot to `FUSION_STATE_PATH`; WebSocket fanout uses Redis when `REDIS_URL` is set
- Field mAP / face TPR / ANPR accuracy need labeled evaluation before operational claims
- Independent security audit + load test at target BOP scale recommended

---

## Tests
```bash
cd central && PYTHONPATH=. pytest tests/ -v
cd ../edge && PYTHONPATH=. pytest tests/ -v
python scripts/eval_metrics.py --gallery-size 500
```

## Documentation
- [Architecture](docs/ARCHITECTURE.md)
- [Deployment](docs/DEPLOYMENT.md)
- [C2 integration](docs/C2_INTEGRATION.md)
