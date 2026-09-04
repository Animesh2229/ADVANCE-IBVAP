import cv2
import time
import yaml
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_pipeline.pipeline import EdgeAIPipeline
from decision.alert_engine import AlertEngine

def load_config(path="configs/edge_config.yaml"):
    # Try multiple possible locations
    possible_paths = [
        path,
        os.path.join(os.path.dirname(__file__), "configs", "edge_config.yaml"),
        os.path.join(os.path.dirname(__file__), "..", "configs", "edge_config.yaml"),
    ]
    for p in possible_paths:
        if os.path.exists(p):
            with open(p) as f:
                return yaml.safe_load(f)
    # Default config
    return {
        "mode": "low_bandwidth",
        "camera": {"source": 0, "camera_id": "BOP-001-CAM-01"},
        "virtual_fence": {"enabled": True, "points": [[200,120],[900,120],[900,600],[200,600]]},
        "central": {"url": "http://localhost:8000/api/v1/alerts/secure"}
    }

def main():
    config = load_config()
    mode = config.get("mode", "low_bandwidth")
    cam_cfg = config.get("camera", {})
    camera_source = cam_cfg.get("source", 0)
    camera_id = cam_cfg.get("camera_id", "BOP-001-CAM-01")

    print(f"[IBVAP] Starting in **{mode.upper()}** mode")
    print(f"[IBVAP] Camera ID: {camera_id}")

    pipeline = EdgeAIPipeline(config)
    alerter = AlertEngine(central_url=config.get("central", {}).get("url"))

    fence_points = None
    if config.get("virtual_fence", {}).get("enabled"):
        fence_points = config["virtual_fence"].get("points")

    cap = cv2.VideoCapture(camera_source)
    if not cap.isOpened():
        print(f"ERROR: Cannot open camera source: {camera_source}")
        return

    print("[IBVAP] Pipeline running... Press 'q' to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Frame failed, retrying...")
            time.sleep(0.3)
            continue

        result = pipeline.process(frame, camera_id, virtual_fence_points=fence_points)

        alerts = alerter.evaluate_from_pipeline(result)

        for alert in alerts:
            print(f"\n[ALERT] {alert['type']} | {alert.get('subtype')} | Conf: {alert['confidence']:.2f}")
            secure = alerter.create_secure_alert(alert)
            alerter.send_to_central(secure)

        # Visualization
        vis = frame.copy()
        for obj in result.get("tracked_objects", []):
            x1, y1, x2, y2 = map(int, obj["bbox"])
            color = (0, 255, 0) if obj["label"] == "person" else (0, 165, 255)
            cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
            cv2.putText(vis, f"ID:{obj['track_id']} {obj['label']}", (x1, y1-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

        if fence_points:
            pts = np.array(fence_points, np.int32).reshape((-1, 1, 2))
            cv2.polylines(vis, [pts], True, (0, 0, 255), 2)

        cv2.imshow(f"IBVAP Edge [{mode}]", vis)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[IBVAP] Edge stopped.")

if __name__ == "__main__":
    main()
