"""
=============================================================
Edge AI Pipeline - Main Brain of the Edge Device
=============================================================
Yeh file poora AI processing flow control karti hai.
Ek frame aata hai → Night enhance → Detect → Track → Face/ANPR/Fence → Result

Easy language mein: Camera se image aati hai, is pipeline se guzarti hai,
aur last mein alerts ke liye ready data milta hai.
"""

import cv2
import time
import numpy as np
from typing import Dict, List, Optional

# Apne modules import kar rahe hain
from .detector import ObjectDetector          # Object detect karta hai (person, car etc.)
from .tracker import MultiObjectTracker       # Objects ko frame-to-frame track karta hai
from .face_engine import FaceEngine           # Face detect + embedding nikalta hai
from .anpr_engine import ANPREngine           # Number plate padhta hai
from .intrusion import VirtualFence           # Virtual boundary check karta hai
from .night import NightEnhancer              # Raat ke time image clear karta hai
from .appearance import extract_color_histogram  # Clothing color hist for cross-camera Re-ID


class EdgeAIPipeline:
    """
    Main Pipeline Class
    -------------------
    Saare AI modules ko load karta hai aur ek saath chalata hai.
    """

    def __init__(self, config: dict = None):
        """
        Pipeline ko start karte time saare models load hote hain.
        Pehli baar thoda time lag sakta hai (models download/load hone mein).
        """
        self.config = config or {}
        print("[Pipeline] Loading models...")

        # Object Detector (YOLOv11) - person, car, truck etc. detect karta hai
        self.detector = ObjectDetector(
            model_path=self.config.get("ai", {}).get("detector_model", "yolo11n.pt")
        )

        # Tracker - same object ko alag frames mein pehchanta hai (ID deta hai)
        self.tracker = MultiObjectTracker()

        # Face Engine - chehre detect karta hai aur unique embedding banata hai
        self.face_engine = FaceEngine()

        # ANPR - Number plate padhne ke liye (India, Nepal, Bhutan support)
        self.anpr = ANPREngine()

        # Virtual Fence - predefined area mein ghusne pe alert
        self.fence = VirtualFence()

        # Night Enhancer - low light mein image improve karta hai
        self.night = NightEnhancer()

        # Kitne frames process hue, count rakhne ke liye
        self.frame_count = 0
        print("[Pipeline] All modules loaded successfully")

    def process(self, frame: np.ndarray, camera_id: str, virtual_fence_points: List = None) -> Dict:
        """
        Ek frame ko process karta hai aur result return karta hai.

        Parameters:
        -----------
        frame : Camera se aaya hua image (numpy array)
        camera_id : Kaunsa camera hai (example: "BOP-001-CAM-01")
        virtual_fence_points : Virtual boundary ke points (optional)

        Returns:
        --------
        Dictionary jisme detected objects, faces, plates, intrusions etc. hote hain
        """
        self.frame_count += 1
        start = time.time()

        # Step 1: Agar raat hai to image enhance karo
        enhanced_frame, is_night = self.night.enhance(frame)

        # Step 2: Objects detect karo (person, vehicle etc.)
        detections = self.detector.detect(enhanced_frame)

        # Step 3: Detected objects ko track karo (ID assign + movement track)
        tracked_objects = self.tracker.update(detections, enhanced_frame)

        # Attach lightweight appearance (color histogram) for cross-camera Re-ID
        for obj in tracked_objects:
            if obj.get("label") == "person" and obj.get("confidence", 0) > 0.55:
                hist = extract_color_histogram(enhanced_frame, obj.get("bbox"))
                if hist:
                    obj["color_histogram"] = hist

        # Step 4: Sirf persons pe face detection chalao
        faces = []
        for obj in tracked_objects:
            if obj["label"] == "person" and obj["confidence"] > 0.6:
                face_result = self.face_engine.process(enhanced_frame, obj["bbox"])
                if face_result:
                    face_result["track_id"] = obj["track_id"]
                    faces.append(face_result)

        # Step 5: Vehicles pe Number Plate Recognition chalao
        plates = []
        for obj in tracked_objects:
            if obj["label"] in ["car", "truck", "bus", "motorcycle"] and obj["confidence"] > 0.55:
                plate = self.anpr.recognize(enhanced_frame, obj["bbox"])
                if plate:
                    plate["track_id"] = obj["track_id"]
                    plates.append(plate)

        # Step 6: Virtual Fence check (agar enabled hai)
        intrusions = []
        if virtual_fence_points:
            intrusions = self.fence.check(tracked_objects, virtual_fence_points)

        # Step 7: Suspicious activity check
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
        """
        Behavior-aware suspicious activity detector (jury-critical upgrade).
        - CRAWLING / CROUCHING: aspect ratio stays flat for several frames
        - SUSPICIOUS_LOITERING: very low pixel velocity
        - FAST_MOVEMENT: high speed
        """
        suspicious = []
        for obj in tracked_objects:
            if obj.get("label") != "person":
                continue

            if obj.get("is_crawling"):
                suspicious.append({
                    "type": "CRAWLING",
                    "track_id": obj["track_id"],
                    "label": "person",
                    "confidence": 0.82,
                    "aspect_ratio": obj.get("aspect_ratio"),
                    "priority_hint": "HIGH",
                })
                continue

            if obj.get("is_slow_loitering"):
                suspicious.append({
                    "type": "SUSPICIOUS_LOITERING",
                    "track_id": obj["track_id"],
                    "label": "person",
                    "confidence": 0.78,
                    "speed": obj.get("speed"),
                    "priority_hint": "MEDIUM",
                })
                continue

            if obj.get("speed", 0) > 25:
                suspicious.append({
                    "type": "FAST_MOVEMENT",
                    "track_id": obj["track_id"],
                    "label": "person",
                    "confidence": 0.7,
                    "speed": obj.get("speed"),
                })
        return suspicious
