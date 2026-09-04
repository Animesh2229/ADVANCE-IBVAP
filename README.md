# ADVANCE-IBVAP

**Intelligent Border Video Analytics Platform**

AI-Based Intelligent Video Analytics Platform for Border Surveillance using existing CCTV Infrastructure.

**Problem Statement ID:** 26187  
**Organization:** Ministry of Home Affairs  
**Department:** Sashastra Seema Bal (SSB)  
**Category:** Software  
**Theme:** Blockchain & Cybersecurity

---

## Features

- Human & Vehicle Detection + Tracking
- Face Detection
- ANPR (India + Nepal + Bhutan support)
- Virtual Fence Intrusion Detection
- Night / Low-light Enhancement
- Real-time Alerts
- Role-based Access (Admin, Commander, Operator, Patroller)
- Vehicle Watchlist
- Multi-camera ready
- Low-Bandwidth mode for remote BOPs
- HQ Dashboard + Field App structure

---

## Project Structure

```
ADVANCE-IBVAP/
├── edge/                  # Edge AI Pipeline
├── central/               # FastAPI Backend
├── dashboard/             # React HQ Dashboard
├── field-app/             # Mobile App starter
├── configs/               # Configuration
├── scripts/               # Setup & start scripts
├── docs/                  # Architecture & Deployment docs
├── docker-compose.yml
└── README.md
```

---

## Quick Start

### 1. Clone
```bash
git clone https://github.com/Animesh2229/ADVANCE-IBVAP.git
cd ADVANCE-IBVAP
```

### 2. Central + Database
```bash
docker-compose up -d
cd central
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python create_admin.py
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Dashboard
```bash
cd dashboard
npm install
npm run dev
```
Open http://localhost:5173  
Login: **admin** / **Admin@123**

### 4. Edge
```bash
cd edge
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main_edge.py
```

---

## Default Login
- Username: `admin`
- Password: `Admin@123`

---

## Tech Stack
- **Edge:** Python, YOLOv11, OpenCV, PaddleOCR
- **Backend:** FastAPI, PostgreSQL, JWT
- **Frontend:** React, Vite, Tailwind CSS
- **Infra:** Docker

---

## Notes
This is an advanced working prototype developed for Smart India Hackathon / SSB problem statement.  
Suitable for demonstration and further production hardening.
