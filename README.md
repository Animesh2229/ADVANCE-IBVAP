# ADVANCE-IBVAP

**Intelligent Border Video Analytics Platform**

AI-Based Intelligent Video Analytics Platform for Border Surveillance using existing CCTV Infrastructure.

## Project for
- Ministry of Home Affairs
- Sashastra Seema Bal (SSB)

## Features
- Human & Vehicle Detection + Tracking
- Face Detection (InsightFace)
- ANPR (India + Nepal + Bhutan support)
- Virtual Fence Intrusion Detection
- Night / Low-light enhancement
- Real-time Alerts
- Role-based Access (Admin, Commander, Operator, Patroller)
- Multi-camera Central Fusion
- Vehicle Watchlist
- Low-Bandwidth mode for remote BOPs
- Field Mobile App support

## Quick Start

### 1. Central + Database
```bash
docker-compose up -d
cd central
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python create_admin.py
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Dashboard
```bash
cd dashboard
npm install
npm run dev
```
Login: `admin` / `Admin@123`

### 3. Edge
```bash
cd edge
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install insightface paddleocr paddlepaddle onnxruntime pyyaml
python main_edge.py
```

## Modes
- `full` → High performance Edge
- `low_bandwidth` → Remote BOP friendly

## Important
This is an advanced working prototype / production-oriented software foundation.
Real field deployment still requires hardware testing, security audit, and official approvals.
