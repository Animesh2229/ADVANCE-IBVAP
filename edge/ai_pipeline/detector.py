"""
Object Detector (YOLOv11) with graceful fallback.

If ultralytics / weights are missing, detection returns [] instead of crashing import.
"""
from typing import List, Dict
import numpy as np


class ObjectDetector:
    def __init__(self, model_path: str = "yolo11n.pt"):
        self.model = None
        self.target_classes = {0: "person", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
        try:
            from ultralytics import YOLO
            print(f"[Detector] Loading model: {model_path}")
            self.model = YOLO(model_path)
            print("[Detector] Model loaded successfully")
        except Exception as e:
            print(f"[Detector] YOLO unavailable ({e}). Detection disabled until model is installed.")

    def detect(self, frame: np.ndarray) -> List[Dict]:
        if self.model is None:
            return []

        results = self.model(frame, verbose=False)[0]
        detections = []
        if results.boxes is None:
            return detections

        for box in results.boxes:
            cls_id = int(box.cls[0])
            if cls_id not in self.target_classes:
                continue
            conf = float(box.conf[0])
            if conf < 0.4:
                continue
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append({
                "bbox": [x1, y1, x2, y2],
                "confidence": conf,
                "label": self.target_classes[cls_id],
            })
        return detections
