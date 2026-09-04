import cv2
import numpy as np
from typing import List, Dict

class VirtualFence:
    def check(self, tracked_objects: List[Dict], fence_points: List[List[int]]) -> List[Dict]:
        if not fence_points or len(fence_points) < 3:
            return []

        intrusions = []
        polygon = np.array(fence_points, dtype=np.int32)

        for obj in tracked_objects:
            cx, cy = obj["centroid"]
            result = cv2.pointPolygonTest(polygon, (float(cx), float(cy)), False)
            if result >= 0:
                intrusions.append({
                    "type": "VIRTUAL_FENCE_INTRUSION",
                    "track_id": obj["track_id"],
                    "label": obj["label"],
                    "confidence": obj["confidence"],
                    "centroid": obj["centroid"]
                })
        return intrusions
