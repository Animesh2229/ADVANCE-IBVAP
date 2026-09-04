#!/bin/bash
echo "======================================"
echo "   IBVAP Setup Script"
echo "======================================"

sudo apt update
sudo apt install -y python3-pip python3-venv docker.io docker-compose git curl

sudo systemctl enable docker
sudo systemctl start docker

echo "Starting database..."
docker-compose up -d

sleep 8

cd central
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python create_admin.py

echo ""
echo "======================================"
echo " Setup Completed!"
echo "Admin: admin / Admin@123"
echo "======================================"
