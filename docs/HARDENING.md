# IBVAP Hardening Notes (post-prototype improvements)

This document summarizes practical hardening applied to the reference implementation.

## 1. Security

- **WebSocket `/ws/alerts`**
  - Requires valid JWT (query `token` **or** `access_token` cookie).
  - Validates user still exists and `is_active`.
  - Checks `Origin` against `ALLOWED_ORIGINS`.
- Edge → Central path already uses **Fernet + HMAC** + replay guard + per-camera rate limit.
- Production refuses to start without a strong `SECRET_KEY`.

**Operational checklist**
- Set strong `SECRET_KEY`, `EDGE_FERNET_KEY`, `EDGE_HMAC_SECRET`, `ADMIN_PASSWORD`.
- Restrict `ALLOWED_ORIGINS` to real dashboard origins.
- Prefer VPN / private network for Edge ↔ Central.
- Run independent security audit + penetration test before field use.

## 2. False-positive reduction

- Detector: higher base confidence, **minimum bbox area**, person aspect-ratio filter, only person+vehicle classes.
- Tracker: requires **≥ 3 hits** and currently visible before emitting a track.
- Alert engine:
  - Night-time raises confidence floor.
  - Per-track de-duplication (~8 s).
  - Ignores non-target labels and low-hit tracks.
- Night / adverse module: CLAHE + denoise + gamma for dark / low-contrast frames.

## 3. Offline / weak network

- Offline queue is **priority-aware** (HIGH flushed first).
- Old items (>24 h) discarded.
- Bad signature / replay responses cause discard (no infinite retry of poisoned items).
- Larger queue capacity with controlled drop of LOW items under pressure.

## 4. Remaining real-world limits (cannot be fully “coded away”)

- Heavy fog / dust / torrential rain still degrades optical sensors.
- Final action decision remains with human operators (by design).
- Cost, physical maintenance, legal/privacy policy.
- Full operational accuracy needs labeled field evaluation (mAP, face TPR, ANPR).

## 5. Recommended next steps for SSB deployment

1. Collect labeled border footage under day/night/fog conditions and run `scripts/eval_metrics.py`.
2. Load-test with `scripts/load_test_bops.py` at target camera count.
3. Independent security audit.
4. Deploy behind VPN + TLS termination + network segmentation.
5. Tune virtual-fence polygons and confidence thresholds per BOP.
