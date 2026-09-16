# IBVAP – Jury Defense Order (Priority Complete)

## What is production-oriented vs prototype

| Area | Claim you can make | Do NOT claim |
|------|-------------------|--------------|
| Detection + tracking | YOLOv11 + SORT-style Kalman works on standard CCTV | Field mAP on fog/dust without your eval |
| Behavior | Crawling / crouching + slow loitering heuristics | Full action recognition (SlowFast etc.) |
| Offline resilience | Priority pruning when disk <10%; exponential backoff | Infinite offline storage |
| Multi-cam fusion | Face + plate + color hist + topology gate | Perfect Re-ID in all lighting |
| Security | HMAC + Fernet + replay guard + hash-chain audit | Formal penetration test done |
| Languages | EN / HI / NE / DZ on dashboard + field app | Professional linguistic certification for Dzongkha |
| Live video | WebSocket alerts; WebRTC signaling API ready | Full multi-cam zero-lag WebRTC media path without aiortc wire-up |

## Demo script (10 minutes)

1. **Language** – Switch Hindi → Nepali → Dzongkha on login + dashboard (border relevance).
2. **Crawling** – Show flat bbox → HIGH `CRAWLING` alert (localized).
3. **Offline** – Kill network → queue fills → free space drops → LOW pruned, HIGH kept.
4. **Fusion** – Same clothing hist across two cams → same global_id.
5. **Security** – Show `/api/v1/chain/verify` and secure alert headers.
6. **Honesty** – “Prototype for field accuracy; architecture and resilience are deploy-oriented.”

## Edge optimization (next ops step)

- Prefer `yolo11n.pt` on constrained BOPs.
- Optional: TensorRT / OpenVINO export after you freeze weights.
- Night enhancer already in pipeline; keep virtual fence points per camera in config.

## Config checklist before field trial

```bash
cp .env.example .env   # SECRET_KEY, EDGE_FERNET_KEY, EDGE_HMAC_SECRET
export CAMERA_TOPOLOGY_PATH=configs/camera_topology.example.json
# Edit topology JSON to real adjacent camera IDs
```

## Files added/updated in this defense pass

- Dashboard: Login + Navbar + Dashboard i18n (en/hi/ne/dz)
- Field-app: LanguageProvider + Login + Home screens
- Central: WebRTC signaling stub (`/api/v1/webrtc/*`)
- Fusion: topology loader + color histogram Re-ID
- Edge: crawling/loitering, storage prune, backoff
- CI: resilient env + npm
- Docs: DRAWBACKS_AND_FIXES, UPGRADES_JURY, DEFENSE_READY
