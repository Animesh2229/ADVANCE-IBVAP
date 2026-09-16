# Windows run (no Docker)

## Tools
- Python 3.11+
- Node.js 20+ LTS
- PostgreSQL 14+ (pgAdmin or SQL Shell)

## Steps
1. Prefer branch `defense/jury-upgrades-v1.3.2` until merged to main.
2. Copy `.env.example` → `.env` and set keys.
3. Create DB:
   ```sql
   CREATE USER ibvap WITH PASSWORD 'ibvap';
   CREATE DATABASE ibvap OWNER ibvap;
   ```
4. Central (CMD):
   ```cmd
   cd central
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python create_admin.py
   uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
   ```
5. Dashboard:
   ```cmd
   cd dashboard
   npm install --legacy-peer-deps
   npm run dev
   ```
6. Edge:
   ```cmd
   cd edge
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   set EDGE_FERNET_KEY=...
   set EDGE_HMAC_SECRET=...
   python main_edge.py
   ```
7. Offline video: set `source: "C:\\path\\demo.mp4"` in `configs/edge_config.yaml`.

**Note:** Use `venv\Scripts\activate` — not `source venv/bin/activate`.
