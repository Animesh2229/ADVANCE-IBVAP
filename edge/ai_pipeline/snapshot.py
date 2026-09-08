"""
Snapshot helper: resize + JPEG compress for LOW bandwidth alerts.
"""
from __future__ import annotations

from typing import Optional, Tuple
import numpy as np

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None


def make_thumbnail(
    frame: np.ndarray,
    max_width: int = 640,
    quality: int = 70,
) -> Optional[bytes]:
    if frame is None or cv2 is None:
        return None
    h, w = frame.shape[:2]
    if w > max_width:
        scale = max_width / float(w)
        frame = cv2.resize(frame, (max_width, int(h * scale)), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    if not ok:
        return None
    return buf.tobytes()
