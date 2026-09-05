"""
=============================================================
Night Enhancement Module
=============================================================
Raat ke time ya low-light condition mein image ko clear banata hai.
CLAHE technique use hoti hai jo contrast improve karti hai.
"""

import cv2
import numpy as np


class NightEnhancer:
    """
    Low light images ko enhance karta hai taaki detection better ho.
    """

    def __init__(self, brightness_threshold=45):
        """
        brightness_threshold: Isse kam average brightness = Night maana jayega
        """
        self.brightness_threshold = brightness_threshold

    def enhance(self, frame: np.ndarray):
        """
        Frame ko check karta hai aur agar dark hai to enhance karta hai.

        Returns:
        --------
        enhanced_frame : Improved image
        is_night       : True agar raat detect hui
        """
        # Image ko grayscale mein convert karke average brightness nikalte hain
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        is_night = brightness < self.brightness_threshold

        if is_night:
            # LAB color space mein convert karo (L = Lightness)
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)

            # CLAHE apply karo - yeh local contrast improve karta hai
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)

            # Wapas merge karke BGR mein convert
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            return enhanced, True

        # Agar din hai to original frame hi return karo
        return frame, False
