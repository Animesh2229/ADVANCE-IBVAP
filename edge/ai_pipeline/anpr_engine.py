import cv2
import numpy as np
import re

class ANPREngine:
    def __init__(self):
        self.ocr = None
        try:
            from paddleocr import PaddleOCR
            self.ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            print("[ANPR] PaddleOCR loaded")
        except Exception as e:
            print(f"[ANPR] PaddleOCR not available ({e}). Running in dummy mode.")

        self.patterns = {
            "IND": [r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{4}$', r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{1,4}$'],
            "NPL": [r'^[0-9]{1,2}[A-Z]{1,3}[0-9]{1,4}$', r'^[A-Z]{1,2}[0-9]{1,4}[A-Z]{0,2}$'],
            "BTN": [r'^[A-Z]{1,3}[0-9]{1,4}$', r'^[0-9]{1,2}[A-Z]{1,3}[0-9]{1,3}$']
        }

    def _clean_text(self, text: str) -> str:
        return re.sub(r'[^A-Z0-9]', '', text.upper())

    def _detect_country(self, plate: str) -> str:
        for country, patterns in self.patterns.items():
            for pat in patterns:
                if re.match(pat, plate):
                    return country
        return "UNKNOWN"

    def recognize(self, frame: np.ndarray, vehicle_bbox: list):
        x1, y1, x2, y2 = map(int, vehicle_bbox)
        x1, y1 = max(0, x1), max(0, y1)
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0 or roi.shape[0] < 25 or roi.shape[1] < 60:
            return None

        if self.ocr is None:
            return None

        try:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            result = self.ocr.ocr(gray, cls=True)
            if not result or not result[0]:
                return None

            best_text, best_conf = "", 0
            for line in result[0]:
                text, conf = line[1]
                cleaned = self._clean_text(text)
                if len(cleaned) >= 6 and conf > best_conf:
                    best_text = cleaned
                    best_conf = conf

            if len(best_text) < 6:
                return None

            return {
                "plate": best_text,
                "confidence": round(float(best_conf), 3),
                "country": self._detect_country(best_text),
                "bbox": vehicle_bbox
            }
        except Exception:
            return None
