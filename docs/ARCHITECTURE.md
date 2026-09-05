# IBVAP Architecture (v1.1)

## High Level Flow

```
Existing CCTV (RTSP / ONVIF)
            ↓
┌────────────────────────────────────────┐
│         Edge Device (BOP)            │
│  • YOLOv11 Detection + Tracking      │
│  • Face (InsightFace / OpenCV)       │
│  • ANPR (PaddleOCR – IND/NPL/BTN)    │
│  • Virtual Fence + Night Enhance     │
│  • Local Decision Engine             │
│  • Secure Encrypted Alert            │
└────────────────────────────────────────┘
            ↓  HTTPS (signed + encrypted)
┌────────────────────────────────────────┐
│         Central Server               │
│  • FastAPI + WebSocket               │
│  • PostgreSQL + JWT + RBAC           │
│  • Multi-Camera Fusion Engine        │
│  • Alert Hub + Vehicle Watchlist     │
│  • Structured Logging + Request ID   │
└────────────────────────────────────────┘
       ↓                    ↓
┌─────────────┐      ┌─────────────────┐
│  HQ Dashboard│      │  Field Mobile   │
│  React + WS  │      │  Expo (RN)      │
│  Real-time   │      │  Jawans App     │
└─────────────┘      └─────────────────┘
```

## Modes
- **Full Edge Mode** – Full AI pipeline on edge device
- **Low-Bandwidth Edge Mode** – Reduced frequency / selective transmission

## Security
- JWT Authentication + Role-based Access Control (admin / commander / operator)
- Encrypted + Signed Alerts (Fernet + SHA256)
- Rate-limited Login
- Security Headers (HSTS, X-Frame-Options, etc.)
- CORS restricted to allowed origins
- Request ID tracing
- Secrets via environment variables only

## Real-time
- WebSocket endpoint `/ws/alerts` for live push to Dashboard
- Automatic fallback to polling if WebSocket unavailable
- Field App uses efficient polling (8s) + pull-to-refresh

## Multi-Camera Fusion
- Face embedding cosine similarity matching
- License plate based association
- Global track ID across cameras
- Time-window based active tracks

## Components

| Component     | Tech                              | Location      |
|---------------|-----------------------------------|---------------|
| Edge AI       | Python, YOLO, OpenCV, InsightFace, PaddleOCR | `edge/`      |
| Central API   | FastAPI, SQLAlchemy, PostgreSQL, WebSocket   | `central/`   |
| Dashboard     | React 18, Vite, Tailwind, WebSocket          | `dashboard/` |
| Field App     | React Native (Expo)                          | `field-app/` |
| Orchestration | Docker Compose                               | root         |
