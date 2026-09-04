#!/bin/bash
echo "Starting IBVAP Central..."
docker-compose up -d db
sleep 5
cd central
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
python create_admin.py
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
