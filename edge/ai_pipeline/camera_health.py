"""
Camera health / integrity checks for border CCTV.
Detects: no-signal, black frame, frozen frame, very low contrast.
Emits health events that AlertEngine can promote to alerts.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple
import time
import numpy as np

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None


class CameraHealthMonitor:
    def __init__(
        self,
        black_mean_threshold: float = 12.0,
        freeze_seconds: float = 8.0,
        min_contrast: float = 6.0,
        check_every_n: int = 15,
    ):
        self.black_mean_threshold = black_mean_threshold
        self.freeze_seconds = freeze_seconds
        self.min_contrast = min_contrast
        self.check_every_n = check_every_n
        self._frame_i = 0
        self._last_hash: Optional[int] = None
        self._freeze_since: Optional[float] = None
        self._last_status = "OK"

    def _frame_hash(self, frame: np.ndarray) -> int:
        small = frame[::16, ::16]
        return hash(small.tobytes())

    def check(self, frame: Optional[np.ndarray], camera_id: str) -> Dict:
        self._frame_i += 1
        now = time.time()
        status = "OK"
        detail = ""

        if frame is None or (hasattr(frame, "size") and frame.size == 0):
            status = "NO_SIGNAL"
            detail = "empty_frame"
            self._last_status = status
            return {
                "camera_id": camera_id,
                "status": status,
                "detail": detail,
                "timestamp": now,
                "priority": "HIGH" if status != "OK" else "LOW",
            }

        if self._frame_i % self.check_every_n != 0 and self._last_status == "OK":
            h = self._frame_hash(frame)
            if self._last_hash is not None and h == self._last_hash:
                if self._freeze_since is None:
                    self._freeze_since = now
                elif now - self._freeze_since >= self.freeze_seconds:
                    status = "FROZEN"
                    detail = f"same_frame>{self.freeze_seconds}s"
            else:
                self._freeze_since = None
            self._last_hash = h
            if status == "OK":
                return {
                    "camera_id": camera_id,
                    "status": "OK",
                    "detail": "",
                    "timestamp": now,
                    "priority": "LOW",
                }

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if cv2 is not None else frame.mean(axis=2).astype(np.uint8)
        mean = float(np.mean(gray))
        std = float(np.std(gray))

        if mean < self.black_mean_threshold:
            status = "BLACK_SIGNAL"
            detail = f"mean={mean:.1f}"
        elif std < self.min_contrast:
            status = "LOW_CONTRAST"
            detail = f"std={std:.1f}"
        else:
            h = self._frame_hash(frame)
            if self._last_hash is not None and h == self._last_hash:
                if self._freeze_since is None:
                    self._freeze_since = now
                elif now - self._freeze_since >= self.freeze_seconds:
                    status = "FROZEN"
                    detail = f"same_frame>{self.freeze_seconds}s"
            else:
                self._freeze_since = None
            self._last_hash = h

        self._last_status = status
        priority = "HIGH" if status in ("NO_SIGNAL", "BLACK_SIGNAL", "FROZEN") else (
            "MEDIUM" if status == "LOW_CONTRAST" else "LOW"
        )
        return {
            "camera_id": camera_id,
            "status": status,
            "detail": detail,
            "timestamp": now,
            "priority": priority,
            "brightness": round(mean, 1),
            "contrast": round(std, 1),
        }
