# ADVANCE-IBVAP – Drawbacks & Full Fixes (Jury Ready)

## Original Critical Drawbacks → Status

| # | Drawback | Risk | Fix Applied | Status |
|---|----------|------|-------------|--------|
| 1 | No real behavior/action recognition | Crawling missed | Aspect-ratio + velocity → CRAWLING / SUSPICIOUS_LOITERING | FIXED |
| 2 | Offline queue can fill disk | Edge crash | Storage-aware priority pruning | FIXED |
| 3 | Primitive multi-camera fusion | ID switch | Color histogram Re-ID + topology gate | FIXED |
| 4 | No network resilience | Central overload | Exponential backoff + jitter | FIXED |
| 5 | WebSocket video lag | Poor live demo | WebRTC signaling path documented | Documented |
| 6 | No field mAP on border data | Over-claim | Honesty note kept | Acknowledged |
| 7 | Scale / GPU unknown | Device crash | yolo11n + notes | Documented |
| 8 | UI only English | Ops friction | EN / HI / NE / DZ | FIXED |

## Languages (Indo-Nepal & Indo-Bhutan)

| Code | Language | Use |
|------|----------|-----|
| en | English | HQ |
| hi | Hindi | Indian SSB |
| ne | Nepali | Indo-Nepal |
| dz | Dzongkha | Indo-Bhutan |

## Remaining honest limits

1. Field accuracy not measured on real fog/dust footage.
2. WebRTC media path needs aiortc wire-up for production.
3. Camera topology must be configured per BOP.
4. Dzongkha UI-level translations; linguistic review recommended.
