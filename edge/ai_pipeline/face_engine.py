import cv2
import numpy as np

class FaceEngine:
    """Uses OpenCV cascade for lightweight prototype. Replace with InsightFace for production."""
    def __init__(self):
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            print("[FaceEngine] Ready (OpenCV cascade - replace with InsightFace for production)")
        except Exception as e:
            print(f"[FaceEngine] Warning: {e}")
            self.face_cascade = None

    def process(self, frame: np.ndarray, person_bbox: list):
        if self.face_cascade is None:
            return None
        x1, y1, x2, y2 = map(int, person_bbox)
        x1, y1 = max(0, x1), max(0, y1)
        person_roi = frame[y1:y2, x1:x2]
        if person_roi.size == 0:
            return None

        gray = cv2.cvtColor(person_roi, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        if len(faces) == 0:
            return None

        fx, fy, fw, fh = max(faces, key=lambda f: f[2]*f[3])
        abs_box = [x1+fx, y1+fy, x1+fx+fw, y1+fy+fh]

        # Placeholder embedding (replace with real InsightFace embedding)
        embedding = np.random.rand(512).astype(np.float32)
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)

        return {
            "bbox": abs_box,
            "embedding": embedding.tolist(),
            "confidence": 0.85,
            "quality": "medium"
        }
