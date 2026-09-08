"""
Object Detector (YOLOv11) with graceful fallback + noise filters.

Filters:
- Confidence threshold
- Minimum bounding-box area (reduces leaf/shadow false positives)
- Target classes only (person + vehicles)
"""
from typing import List, Dict
import numpy as np


class ObjectDetector:
    def __init__(self, model_path: str = "yolo11n.pt", min_conf: float = 0.45, min_area: int = 900):
        self.model = None
        self.min_conf = min_conf
        self.min_area = min_area
        # COCO: person + common vehicles only (ignore animals, bags, etc.)
        self.target_classes = {0: "person", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
        try:
            from ultralytics import YOLO
            print(f"[Detector] Loading model: {model_path}")
            self.model = YOLO(model_path)
            print("[Detector] Model loaded successfully")
        except Exception as e:
            print(f"[Detector] YOLO unavailable ({e}). Detection disabled until model is installed.")

    def detect(self, frame: np.ndarray) -> List[Dict]:
        if self.model is None or frame is None or frame.size == 0:
            return []

        results = self.model(frame, verbose=False)[0]
        detections = []
        if results.boxes is None:
            return detections

        h, w = frame.shape[:2]
        for box in results.boxes:
            cls_id = int(box.cls[0])
            if cls_id not in self.target_classes:
                continue
            conf = float(box.conf[0])
            if conf < self.min_conf:
                continue
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            # Clamp
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w - 1, x2), min(h - 1, y2)
            area = max(0, (x2 - x1) * (y2 - y1))
            if area < self.min_area:
                continue  # ignore tiny blobs (noise / distant leaves)
            # Aspect ratio sanity for person
            label = self.target_classes[cls_id]
            bw, bh = (x2 - x1), (y2 - y1)
            if label == "person" and bh > 0:
                ar = bw / bh
                if ar > 1.6 or ar < 0.2:  # unlikely person shape
                    continue
            detections.append({
                "bbox": [x1, y1, x2, y2],
                "confidence": conf,
                "label": label,
            })
        return detections
