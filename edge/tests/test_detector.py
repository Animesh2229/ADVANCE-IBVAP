import numpy as np
from ai_pipeline.detector import ObjectDetector


def test_detector_does_not_crash_without_yolo():
    det = ObjectDetector(model_path="does-not-exist.pt")
    frame = np.zeros((64, 64, 3), dtype=np.uint8)
    out = det.detect(frame)
    assert isinstance(out, list)
