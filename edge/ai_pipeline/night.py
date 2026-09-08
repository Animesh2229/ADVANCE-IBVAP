"""
=============================================================
Night / Adverse Weather Enhancement Module
=============================================================
Low-light, fog-ish and low-contrast frames ko improve karta hai.
CLAHE + optional gamma + mild denoise.
"""

import cv2
import numpy as np


class NightEnhancer:
    """
    Low light / low contrast images ko enhance karta hai taaki detection better ho.
    """

    def __init__(self, brightness_threshold=50, contrast_threshold=35):
        self.brightness_threshold = brightness_threshold
        self.contrast_threshold = contrast_threshold

    def enhance(self, frame: np.ndarray):
        """
        Returns:
            enhanced_frame, is_adverse (night / low-contrast / haze-like)
        """
        if frame is None or frame.size == 0:
            return frame, False

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray))
        contrast = float(np.std(gray))
        is_adverse = brightness < self.brightness_threshold or contrast < self.contrast_threshold

        if not is_adverse:
            return frame, False

        # Mild denoise first (helps with fog/rain noise)
        denoised = cv2.fastNlMeansDenoisingColored(frame, None, 3, 3, 7, 21)

        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # Adaptive CLAHE
        clip = 2.5 if brightness > 30 else 3.5
        clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(8, 8))
        l = clahe.apply(l)

        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

        # Mild gamma correction for very dark frames
        if brightness < 35:
            gamma = 1.25
            inv = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv) * 255 for i in range(256)]).astype("uint8")
            enhanced = cv2.LUT(enhanced, table)

        return enhanced, True
