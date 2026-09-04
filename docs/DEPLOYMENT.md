# Deployment Guide

## Central
1. docker-compose up -d
2. Setup Python venv in central/
3. python create_admin.py
4. uvicorn api.main:app --host 0.0.0.0 --port 8000

## Dashboard
1. cd dashboard && npm install && npm run dev

## Edge
1. cd edge && python -m venv venv && source venv/bin/activate
2. pip install -r requirements.txt
3. python main_edge.py

## Production Notes
- Use HTTPS
- Change default admin password
- Use WireGuard/VPN between Edge and Central
- Enable proper logging and monitoring
