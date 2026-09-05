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

    fence_points = None
    if config.get("virtual_fence", {}).get("enabled"):
        fence_points = config["virtual_fence"].get("points")

    streams = open_cameras(cam_list)
    if not streams:
        print("ERROR: No camera could be opened. Check config / devices / RTSP.")
        return

    print(f"[IBVAP] Running {len(streams)} camera(s). Press 'q' to quit.")

    while True:
        for stream in streams:
            ret, frame = stream["cap"].read()
            if not ret:
                stream["cap"].release()
                stream["cap"] = cv2.VideoCapture(stream["source"])
                continue

            result = pipeline.process(frame, stream["camera_id"], virtual_fence_points=fence_points)
            alerts = alerter.evaluate_from_pipeline(result)

            for alert in alerts:
                print(f"[ALERT] {stream['camera_id']} | {alert['type']} | {alert.get('subtype')} | {alert['confidence']:.2f}")
                secure = alerter.create_secure_alert(alert)
                alerter.send_to_central(secure)

            if stream is streams[0]:
                vis = frame.copy()
                for obj in result.get("tracked_objects", []):
                    x1, y1, x2, y2 = map(int, obj["bbox"])
                    color = (0, 255, 0) if obj["label"] == "person" else (0, 165, 255)
                    cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(vis, f"ID:{obj['track_id']} {obj['label']}", (x1, y1 - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
                if fence_points:
                    pts = np.array(fence_points, np.int32).reshape((-1, 1, 2))
                    cv2.polylines(vis, [pts], True, (0, 0, 255), 2)
                cv2.putText(vis, f"{bop_id} | cams:{len(streams)}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.imshow(f"IBVAP Edge [{bop_id}]", vis)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    for s in streams:
        s["cap"].release()
    cv2.destroyAllWindows()
    print("[IBVAP] Edge stopped.")


if __name__ == "__main__":
    main()
