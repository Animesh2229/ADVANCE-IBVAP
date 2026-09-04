import cv2
import numpy as np

class NightEnhancer:
    def __init__(self, brightness_threshold=45):
        self.brightness_threshold = brightness_threshold

    def enhance(self, frame: np.ndarray):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        is_night = brightness < self.brightness_threshold

        if is_night:
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            l = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(l)
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            return enhanced, True
        return frame, False
