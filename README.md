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
# Set SECRET_KEY (>=32 chars), ADMIN_PASSWORD, EDGE_FERNET_KEY, EDGE_HMAC_SECRET
```

When `ENVIRONMENT=production`, `SECRET_KEY` (>=32 chars) is **required**.

### 3–7
See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for Central, Dashboard, Edge, Field App, Redis, VPN, and scale notes.

---

## Features (v1.3.1+ hardened)

- Human & Vehicle Detection + Tracking (YOLOv11 + **SORT-style Kalman/IoU tracker**)
- Face detection and embeddings to Central (vectorized match + optional FAISS)
- ANPR plates to Central (India / Nepal / Bhutan)
- Virtual Fence + **improved Night / low-contrast enhancement**
- Real-time Alerts via WebSocket (+ Redis pub/sub fanout when configured)
- **Hardened WebSocket auth** (JWT + active user check + Origin allow-list)
- HMAC + Fernet on `/api/v1/alerts/secure` + per-camera rate limiting + replay guard
- Role-based Access Control, httpOnly JWT cookie, forced password change
- Vehicle + Face watchlist
- Multi-camera Fusion with optional `FUSION_STATE_PATH` persistence
- C2 pull export + outbound webhook
- Optional HIGH/MEDIUM alert snapshots from Edge
- **Priority-aware offline alert queue**
- Immutable hash-chain audit log + `/api/v1/chain/verify`
- **False-positive reduction**: min area, aspect filter, multi-hit confirmation, night conf floor, track de-dupe
- CI with real tests; `scripts/eval_metrics.py` micro-benchmarks

---

## Security Notes

- Shared `EDGE_FERNET_KEY` + `EDGE_HMAC_SECRET` required
- Production hard-fails without `SECRET_KEY`
- Never commit `.env`
- See [docs/HARDENING.md](docs/HARDENING.md) for details of applied hardening

---

## Status & honesty note

Working reference implementation for PS 26187 with practical hardening applied.

Still requires field evaluation before operational border claims:

- Collect labeled day/night/fog footage and measure mAP / face TPR / ANPR accuracy
- Independent security audit + load test at target BOP scale
- VPN / network segmentation for Edge ↔ Central

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
- [Hardening](docs/HARDENING.md)
