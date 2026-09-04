# ADVANCE-IBVAP

**Intelligent Border Video Analytics Platform**

AI-Based Intelligent Video Analytics Platform for Border Surveillance using existing CCTV Infrastructure.

**Problem Statement ID:** 26187  
**Organization:** Ministry of Home Affairs  
**Department:** Sashastra Seema Bal (SSB)

---

## Features

- Human & Vehicle Detection + Tracking
- Face Detection
- Automatic Number Plate Recognition (India + Nepal + Bhutan)
- Virtual Fence Intrusion Detection
- Night / Low-light Enhancement
- Real-time Alerts
- Role-based Access (Admin, Commander, Operator, Patroller)
- Vehicle Watchlist
- Multi-camera support ready
- Low-Bandwidth mode for remote BOPs

---

## Project Structure

```
ADVANCE-IBVAP/
├── edge/                 # Edge AI Pipeline
├── central/              # FastAPI Backend
├── dashboard/            # React HQ Dashboard
├── configs/              # Configuration files
├── scripts/              # Start & setup scripts
├── docker-compose.yml
└── README.md
```

---

## Quick Start (Laptop)

### 1. Clone the repository
```bash
git clone https://github.com/Animesh2229/ADVANCE-IBVAP.git
cd ADVANCE-IBVAP
```

### 2. Start Database + Central
```bash
docker-compose up -d

cd central
python -m venv venv

# Linux / Mac
source venv/bin/activate

# Windows
# venv\Scripts\activate

pip install -r requirements.txt
python create_admin.py

uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Start Dashboard
```bash
cd dashboard
npm install
npm run dev
```
Open: http://localhost:5173  
Login: **admin** / **Admin@123**

### 4. Start Edge (Webcam)
```bash
cd edge
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main_edge.py
```

---

## Default Credentials
- Username: `admin`
- Password: `Admin@123`

---

## Tech Stack

**Edge:** Python, YOLOv11, OpenCV, PaddleOCR, Cryptography  
**Central:** FastAPI, PostgreSQL, SQLAlchemy, JWT  
**Dashboard:** React, Vite, Tailwind CSS  
**Infra:** Docker, Docker Compose

---

## Notes

- First run will download YOLO model automatically.
- For real camera, edit `configs/edge_config.yaml` and set RTSP URL.
- This is an advanced working prototype suitable for demo and further development.

---

## License
For educational and authorized government use only.
