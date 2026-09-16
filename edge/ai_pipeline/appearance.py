"""
Lightweight appearance features for cross-camera Re-ID.
Color histogram (HSV) is cheap and works well for clothing-based matching
when face is not visible / cameras are non-overlapping.
"""
from __future__ import annotations

from typing import List, Optional

import numpy as np

try:
    import cv2
    _HAS_CV2 = True
except Exception:
    _HAS_CV2 = False


def extract_color_histogram(frame: np.ndarray, bbox: List[float], bins: int = 16) -> Optional[List[float]]:
    """
    Extract a compact HSV histogram from the person bbox crop.
    Returns a flat list of length bins*3 (H, S, V channels).
    Safe if OpenCV is missing (returns None).
    """
    if not _HAS_CV2 or frame is None or not bbox or len(bbox) < 4:
        return None
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = [int(v) for v in bbox[:4]]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w - 1, x2), min(h - 1, y2)
    if x2 <= x1 or y2 <= y1:
        return None
    crop = frame[y1:y2, x1:x2]
    if crop.size == 0:
        return None
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    hist_h = cv2.calcHist([hsv], [0], None, [bins], [0, 180])
    hist_s = cv2.calcHist([hsv], [1], None, [bins], [0, 256])
    hist_v = cv2.calcHist([hsv], [2], None, [bins], [0, 256])
    hist = np.concatenate([hist_h, hist_s, hist_v]).flatten()
    hist = hist / (hist.sum() + 1e-8)
    return hist.astype(np.float32).tolist()
