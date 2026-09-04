from ultralytics import YOLO
import numpy as np

class ObjectDetector:
    def __init__(self, model_path="yolo11n.pt"):
        self.model = YOLO(model_path)
        self.target_classes = {"person", "car", "truck", "bus", "motorcycle", "bicycle"}

    def detect(self, frame: np.ndarray) -> list:
        results = self.model(frame, verbose=False, conf=0.45)[0]
        detections = []

        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = results.names[cls_id]
            if label not in self.target_classes:
                continue

            detections.append({
                "label": label,
                "confidence": float(box.conf[0]),
                "bbox": box.xyxy[0].cpu().numpy().tolist(),
                "class_id": cls_id
            })
        return detections
