"""
=============================================================
Object Detector Module (YOLOv11)
=============================================================
Yeh module camera frame mein objects detect karta hai.
Person, car, truck, bus, motorcycle etc. pehchanta hai.
Ultralytics YOLOv11 use hota hai (lightweight + accurate).
"""

from ultralytics import YOLO
import numpy as np
from typing import List, Dict


class ObjectDetector:
    """
    YOLOv11 based object detector.
    """

    def __init__(self, model_path: str = "yolo11n.pt"):
        """
        Model load karta hai.
        yolo11n.pt = nano version (fast, edge devices ke liye best)
        """
        print(f"[Detector] Loading model: {model_path}")
        self.model = YOLO(model_path)
        # Hum sirf in classes ko detect karenge (COCO dataset ke IDs)
        # 0=person, 2=car, 3=motorcycle, 5=bus, 7=truck
        self.target_classes = {0: "person", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
        print("[Detector] Model loaded successfully")

    def detect(self, frame: np.ndarray) -> List[Dict]:
        """
        Frame mein objects detect karta hai.

        Returns:
        --------
        List of detections. Har detection mein:
        - bbox: [x1, y1, x2, y2]
        - confidence: 0 se 1
        - label: "person" / "car" etc.
        """
        # YOLO se prediction lo (verbose=False → extra print na aaye)
        results = self.model(frame, verbose=False)[0]

        detections = []
        if results.boxes is None:
            return detections

        for box in results.boxes:
            cls_id = int(box.cls[0])
            # Sirf hamare target classes ko hi lo
            if cls_id not in self.target_classes:
                continue

            conf = float(box.conf[0])
            # Confidence bahut kam ho to skip kar do
            if conf < 0.4:
                continue

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append({
                "bbox": [x1, y1, x2, y2],
                "confidence": conf,
                "label": self.target_classes[cls_id]
            })

        return detections
