@echo off
cd /d %~dp0\..\central
if not exist venv\Scripts\activate.bat (
  python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt
if not defined DATABASE_URL set DATABASE_URL=postgresql+asyncpg://ibvap:ibvap@localhost:5432/ibvap
python create_admin.py
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
