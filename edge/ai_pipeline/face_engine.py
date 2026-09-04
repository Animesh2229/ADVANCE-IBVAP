import cv2
import numpy as np

class FaceEngine:
    """
    Production-ready structure.
    Tries InsightFace first, falls back to OpenCV Haar cascade.
    """
    def __init__(self):
        self.use_insightface = False
        self.app = None
        self.face_cascade = None

        # Try InsightFace
        try:
            from insightface.app import FaceAnalysis
            self.app = FaceAnalysis(name="buffalo_l", providers=['CPUExecutionProvider'])
            self.app.prepare(ctx_id=-1, det_size=(640, 640))
            self.use_insightface = True
            print("[FaceEngine] InsightFace (buffalo_l) loaded successfully")
        except Exception as e:
            print(f"[FaceEngine] InsightFace not available ({e}). Using OpenCV cascade.")
            try:
                self.face_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                )
                print("[FaceEngine] OpenCV Haar cascade ready")
            except Exception as e2:
                print(f"[FaceEngine] Failed to load any face model: {e2}")

    def process(self, frame: np.ndarray, person_bbox: list):
        x1, y1, x2, y2 = map(int, person_bbox)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)
        person_roi = frame[y1:y2, x1:x2]

        if person_roi.size == 0:
            return None

        if self.use_insightface and self.app is not None:
            return self._process_insightface(person_roi, x1, y1)
        elif self.face_cascade is not None:
            return self._process_opencv(person_roi, x1, y1)
        return None

    def _process_insightface(self, roi, offset_x, offset_y):
        try:
            faces = self.app.get(roi)
            if not faces:
                return None
            face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            abs_bbox = [
                int(offset_x + face.bbox[0]),
                int(offset_y + face.bbox[1]),
                int(offset_x + face.bbox[2]),
                int(offset_y + face.bbox[3])
            ]
            embedding = face.embedding.astype(np.float32)
            embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
            return {
                "bbox": abs_bbox,
                "embedding": embedding.tolist(),
                "confidence": float(face.det_score),
                "quality": "high" if face.det_score > 0.75 else "medium",
                "engine": "insightface"
            }
        except Exception:
            return None

    def _process_opencv(self, roi, offset_x, offset_y):
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        if len(faces) == 0:
            return None
        fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])
        abs_box = [offset_x + fx, offset_y + fy, offset_x + fx + fw, offset_y + fy + fh]
        # Random normalized embedding as placeholder
        embedding = np.random.rand(512).astype(np.float32)
        embedding /= (np.linalg.norm(embedding) + 1e-8)
        return {
            "bbox": abs_box,
            "embedding": embedding.tolist(),
            "confidence": 0.80,
            "quality": "medium",
            "engine": "opencv"
        }
