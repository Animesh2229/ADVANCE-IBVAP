"""
=============================================================
IBVAP Edge Device - Main Entry Point (Multi-Camera / 1 BOP)
=============================================================
Ek BOP pe 16 cameras tak support.
Har enabled camera se frame lo → AI Pipeline → Alert → Central

Kaise chalaye:
    python main_edge.py
"""

import cv2
import time
import yaml
import numpy as np
import sys
import os
from typing import List, Dict

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_pipeline.pipeline import EdgeAIPipeline
from decision.alert_engine import AlertEngine


def load_config(path="configs/edge_config.yaml"):
    possible_paths = [
        path,
        os.path.join(os.path.dirname(__file__), "configs", "edge_config.yaml"),
        os.path.join(os.path.dirname(__file__), "..", "configs", "edge_config.yaml"),
    ]
    for p in possible_paths:
        if os.path.exists(p):
            with open(p) as f:
                return yaml.safe_load(f)

    return {
        "mode": "low_bandwidth",
        "bop_id": "BOP-001",
        "cameras": [{"camera_id": "BOP-001-CAM-01", "source": 0, "enabled": True}],
        "virtual_fence": {"enabled": True, "points": [[200, 120], [900, 120], [900, 600], [200, 600]]},
        "central": {"url": "http://localhost:8000/api/v1/alerts/secure"},
    }


def open_cameras(cam_list: List[Dict]) -> List[Dict]:
    """Enabled cameras open karo. Fail hone wale skip."""
    opened = []
    for cam in cam_list:
        if not cam.get("enabled", True):
            continue
        src = cam["source"]
        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            print(f"[WARN] Cannot open {cam['camera_id']} source={src} — skipped")
            continue
        opened.append({"camera_id": cam["camera_id"], "source": src, "cap": cap})
        print(f"[OK] Opened {cam['camera_id']} ← {src}")
    return opened


def main():
    config = load_config()
    mode = config.get("mode", "low_bandwidth")
    bop_id = config.get("bop_id", "BOP-001")

    if "cameras" in config and config["cameras"]:
        cam_list = config["cameras"]
    else:
        c = config.get("camera", {})
        cam_list = [{
            "camera_id": c.get("camera_id", f"{bop_id}-CAM-01"),
            "source": c.get("source", 0),
            "enabled": True,
        }]

    print(f"[IBVAP] BOP={bop_id} | mode={mode.upper()}")
    print(f"[IBVAP] Configured cameras: {len(cam_list)} (max 16)")

    pipeline = EdgeAIPipeline(config)
    alerter = AlertEngine(central_url=config.get("central", {}).get("url"))

    streams = open_cameras(cam_list)
    if not streams:
        print("[FATAL] No cameras opened")
        return

    fence_cfg = config.get("virtual_fence", {})
    fence_points = fence_cfg.get("points") if fence_cfg.get("enabled", True) else None

    print("[IBVAP] Running… Ctrl+C to stop")
    try:
        while True:
            for stream in streams:
                ret, frame = stream["cap"].read()
                if not ret or frame is None:
                    continue
                try:
                    result = pipeline.process(frame, stream["camera_id"], virtual_fence_points=fence_points)
                    alerts = alerter.evaluate_from_pipeline(result)
                    for alert in alerts:
                        print(f"[ALERT] {stream['camera_id']} | {alert['type']} | {alert.get('subtype')} | {alert.get('confidence', 0):.2f}")
                        secure = alerter.create_secure_alert(alert)
                        alerter.send_to_central(secure)
                except Exception as frame_err:
                    print(f"[ERROR] {stream['camera_id']} frame failed: {frame_err}")
                    continue
            time.sleep(0.03)
    except KeyboardInterrupt:
        print("\n[IBVAP] Stopped")
    finally:
        for stream in streams:
            stream["cap"].release()


if __name__ == "__main__":
    main()
