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
# Edit .env and set strong SECRET_KEY and passwords
```

### 3. Start Database + Central
```bash
docker-compose up -d
cd central
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python create_admin.py
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Dashboard
```bash
cd dashboard
npm install
npm run dev
```
Open: http://localhost:5173  
Default Login: `admin` / `Admin@123` (change immediately)

### 5. Edge
```bash
cd edge
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main_edge.py
```

---

## Security Notes

- All secrets must be set via environment variables (see `.env.example`)
- Never commit `.env` file
- Change default admin password before any real deployment
- CORS is restricted to configured origins
- Login has basic rate limiting
- Security headers are added automatically

---

## Features
- Human & Vehicle Detection + Tracking
- Face Detection (InsightFace / OpenCV fallback)
- ANPR (India + Nepal + Bhutan)
- Virtual Fence + Night Enhancement
- Real-time Alerts + Role-based Access
- Vehicle Watchlist
- Multi-camera Fusion structure

---

## Important
This is an advanced working prototype for Smart India Hackathon / demonstration purposes.  
For real SSB deployment, additional field testing, security audit, and hardening are required.
