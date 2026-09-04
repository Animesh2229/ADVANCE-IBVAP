#!/bin/bash
echo "Starting IBVAP Edge..."
cd edge
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
python main_edge.py
