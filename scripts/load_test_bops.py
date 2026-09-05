"""Simulate concurrent BOP alert ingest.\nUsage: python scripts/load_test_bops.py --url http://localhost:8000 --bops 100 --cams 2 --rounds 3\n"""
import argparse
import asyncio
import random
import time
import httpx


async def send_one(client, base, bop, cam):
    payload = {
        "camera_id": f"BOP-{bop:04d}-CAM-{cam:02d}",
        "alert_type": random.choice(["DETECTION", "INTRUSION", "SUSPICIOUS"]),
        "subtype": random.choice(["person", "VIRTUAL_FENCE", "FAST_MOVEMENT"]),
        "confidence": round(random.uniform(0.55, 0.98), 3),
        "priority": random.choice(["LOW", "MEDIUM", "HIGH"]),
        "timestamp": time.time(),
    }
    r = await client.post(f"{base}/api/v1/alerts/secure", json=payload)
    return r.status_code


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--bops", type=int, default=100)
    ap.add_argument("--cams", type=int, default=2)
    ap.add_argument("--rounds", type=int, default=2)
    args = ap.parse_args()

    total = args.bops * args.cams * args.rounds
    ok = fail = 0
    t0 = time.time()
    async with httpx.AsyncClient(timeout=10.0) as client:
        for rnd in range(args.rounds):
            tasks = []
            for b in range(1, args.bops + 1):
                for c in range(1, args.cams + 1):
                    tasks.append(send_one(client, args.url.rstrip("/"), b, c))
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if r == 200:
                    ok += 1
                else:
                    fail += 1
            print(f"round {rnd+1}/{args.rounds}: done")
    dt = time.time() - t0
    print(f"Total={total} OK={ok} FAIL={fail} time={dt:.1f}s rate={total/dt:.1f} req/s")


if __name__ == "__main__":
    asyncio.run(main())
