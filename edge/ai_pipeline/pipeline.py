import cv2
import time
import numpy as np
from typing import Dict, List, Optional
from .detector import ObjectDetector
from .tracker import MultiObjectTracker
from .face_engine import FaceEngine
from .anpr_engine import ANPREngine
from .intrusion import VirtualFence
from .night import NightEnhancer

class EdgeAIPipeline:
    def __init__(self, config: dict = None):
        self.config = config or {}
        print("[Pipeline] Loading models...")
        self.detector = ObjectDetector(model_path=self.config.get("ai", {}).get("detector_model", "yolo11n.pt"))
        self.tracker = MultiObjectTracker()
        self.face_engine = FaceEngine()
        self.anpr = ANPREngine()
        self.fence = VirtualFence()
        self.night = NightEnhancer()
        self.frame_count = 0
        print("[Pipeline] All modules loaded successfully")

    def process(self, frame: np.ndarray, camera_id: str, virtual_fence_points: List = None) -> Dict:
        self.frame_count += 1
        start = time.time()

        enhanced_frame, is_night = self.night.enhance(frame)
        detections = self.detector.detect(enhanced_frame)
        tracked_objects = self.tracker.update(detections, enhanced_frame)

        faces = []
        for obj in tracked_objects:
            if obj["label"] == "person" and obj["confidence"] > 0.6:
                face_result = self.face_engine.process(enhanced_frame, obj["bbox"])
                if face_result:
                    faces.append(face_result)

        plates = []
        for obj in tracked_objects:
            if obj["label"] in ["car", "truck", "bus", "motorcycle"] and obj["confidence"] > 0.55:
                plate = self.anpr.recognize(enhanced_frame, obj["bbox"])
                if plate:
                    plates.append(plate)

        intrusions = []
        if virtual_fence_points:
            intrusions = self.fence.check(tracked_objects, virtual_fence_points)

        suspicious = self._detect_suspicious(tracked_objects)

        inference_time = (time.time() - start) * 1000

        return {
            "camera_id": camera_id,
            "frame_id": self.frame_count,
            "timestamp": time.time(),
            "is_night": is_night,
            "tracked_objects": tracked_objects,
            "faces": faces,
            "plates": plates,
            "intrusions": intrusions,
            "suspicious": suspicious,
            "inference_ms": round(inference_time, 1)
        }

    def _detect_suspicious(self, tracked_objects: List[Dict]) -> List[Dict]:
        suspicious = []
        for obj in tracked_objects:
            if obj["label"] == "person" and obj.get("speed", 0) > 25:
                suspicious.append({
                    "type": "FAST_MOVEMENT",
                    "track_id": obj["track_id"],
                    "label": obj["label"],
                    "confidence": 0.7
                })
        return suspicious
