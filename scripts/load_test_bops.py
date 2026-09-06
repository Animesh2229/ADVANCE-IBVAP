"""Simulate concurrent BOP alert ingest with real HMAC+Fernet.

Requires:
  EDGE_FERNET_KEY
  EDGE_HMAC_SECRET

Usage:
  python scripts/load_test_bops.py --url http://localhost:8000 --bops 100 --cams 2 --rounds 3
"""
import argparse
import asyncio
import os
import random
import sys
import time

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "central"))
from services.edge_auth import encrypt_alert, sign, load_secrets  # noqa: E402


async def send_one(client, base, bop, cam, fkey, hkey):
    alert = {
        "type": random.choice(["DETECTION", "INTRUSION", "SUSPICIOUS", "FACE", "ANPR"]),
        "subtype": random.choice(["person", "VIRTUAL_FENCE", "FAST_MOVEMENT", "FACE_DETECTED", "IND"]),
        "confidence": round(random.uniform(0.55, 0.98), 3),
        "priority": random.choice(["LOW", "MEDIUM", "HIGH"]),
        "camera_id": f"BOP-{bop:04d}-CAM-{cam:02d}",
        "track_id": random.randint(1, 50),
        "timestamp": time.time(),
        "plate": f"UK07AB{random.randint(1000,9999)}" if random.random() > 0.7 else None,
        "embedding": [random.random() for _ in range(8)] if random.random() > 0.7 else None,
    }
    enc = encrypt_alert(alert, fkey)
    ts = str(int(time.time()))
    sig = sign(enc, ts, hkey)
    body = {"encrypted_payload": enc, "camera_id": alert["camera_id"], "timestamp": ts, "signature": sig}
    headers = {"X-IBVAP-Timestamp": ts, "X-IBVAP-Signature": sig}
    r = await client.post(f"{base}/api/v1/alerts/secure", json=body, headers=headers)
    return r.status_code


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--bops", type=int, default=100)
    ap.add_argument("--cams", type=int, default=2)
    ap.add_argument("--rounds", type=int, default=2)
    args = ap.parse_args()

    fkey, hkey = load_secrets()
    total = args.bops * args.cams * args.rounds
    ok = fail = 0
    t0 = time.time()
    async with httpx.AsyncClient(timeout=10.0) as client:
        for rnd in range(args.rounds):
            tasks = [
                send_one(client, args.url.rstrip("/"), b, c, fkey, hkey)
                for b in range(1, args.bops + 1)
                for c in range(1, args.cams + 1)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if r == 200:
                    ok += 1
                else:
                    fail += 1
            print(f"round {rnd+1}/{args.rounds}: done")
    dt = time.time() - t0
    print(f"Total={total} OK={ok} FAIL={fail} time={dt:.1f}s rate={total/max(dt,0.001):.1f} req/s")


if __name__ == "__main__":
    asyncio.run(main())
