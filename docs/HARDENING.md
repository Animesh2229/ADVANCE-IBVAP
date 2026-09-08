# IBVAP Hardening Notes (final package)

## Security
- WebSocket `/ws/alerts`: JWT (query token or cookie) + **active user check** + Origin allow-list
- `POST /api/v1/auth/ws-token`: 15-minute scoped token for WS when cookies unreliable
- Edge → Central: Fernet + HMAC + replay guard + per-camera rate limit
- Production: strong `SECRET_KEY` required; **REDIS_URL strongly recommended** for multi-worker
- VPN / TLS deployment guidance in `DEPLOYMENT.md`

## False-positive reduction
- Detector: min bbox area, person aspect-ratio, class allow-list
- Tracker: ≥3 hits + currently visible
- Alert engine: night conf floor, per-track de-dupe, label filters
- Per-BOP thresholds in `configs/edge_config.yaml`

## Offline / weak network
- Priority-aware offline queue (HIGH first)
- >24h discard; 401/409 poison drop
- Compressed snapshots for HIGH/MEDIUM

## Privacy
- `FACE_EMBEDDING_TTL_HOURS` + startup purge + admin purge endpoint
- `services.pii_redact` for logs/exports
- Watchlist embeddings retained; non-watchlist expire

## Evaluation
- `scripts/eval_metrics.py`: synthetic benches + **field protocol** template
- Do not claim mAP/TPR/ANPR until labeled border data is measured

## Ops
- Model path + optional SHA256 pin in edge config
- CI runs central + edge tests on PR
- Load test script for multi-BOP scale
