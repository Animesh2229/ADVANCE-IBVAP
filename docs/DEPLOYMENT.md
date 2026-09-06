# Deployment Guide (SSB / Police II — low-cost, limited network)

## Central
1. `docker-compose up -d` (Postgres)
2. `cp .env.example .env` and set secrets
3. `cd central && python -m venv venv && source venv/bin/activate`
4. `pip install -r requirements.txt`
5. `python create_admin.py`
6. `uvicorn api.main:app --host 0.0.0.0 --port 8000`

### Production env (required)
```
ENVIRONMENT=production
SECRET_KEY=<long random >=32>
EDGE_FERNET_KEY=<fernet>
EDGE_HMAC_SECRET=<hmac>
DATABASE_URL=postgresql+asyncpg://...
```

### Recommended
```
FUSION_STATE_PATH=/var/lib/ibvap/fusion_state.json
REDIS_URL=redis://localhost:6379/0
C2_WEBHOOK_URL=https://c2.example.gov.in/ingest
ALLOWED_ORIGINS=https://dashboard.example.local
```

## Dashboard
```bash
cd dashboard && npm install && npm run build
```

## Edge (BOP)
```bash
cd edge && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main_edge.py
```
- Local AI on BOP mini-PC; only alerts go to Central (weak links OK).
- Offline queue stores alerts when network drops.

## Security hardening
| Control | How |
|---------|-----|
| Transport | HTTPS; Edge↔Central over WireGuard/VPN |
| Auth | HMAC+Fernet on `/alerts/secure`; JWT httpOnly cookie |
| Secrets | Never commit `.env`; rotate HMAC + Fernet together |
| mTLS (optional) | Client certs at Nginx for Edge subnet |
| Rate limit | Per-camera window; Redis multi-worker |
| Chain audit | `GET /api/v1/chain/verify` |

## Benchmarks
```bash
python scripts/eval_metrics.py --gallery-size 1000 --detections 20
python scripts/load_test_bops.py --bops 50 --cams 2 --rounds 2
```
