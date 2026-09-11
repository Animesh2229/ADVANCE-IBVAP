"""Behavior upgrades: crawling / crouching + slow loitering."""
from ai_pipeline.tracker import MultiObjectTracker


def test_crawling_detection_via_flat_aspect():
    tr = MultiObjectTracker(max_disappeared=20, iou_threshold=0.2)
    # Tall standing person
    for i in range(3):
        tr.update([{"bbox": [100, 50, 140, 200], "label": "person", "confidence": 0.9}])
    # Switch to flat (crawling) box for several frames
    for i in range(8):
        r = tr.update([{"bbox": [100, 150, 200, 180], "label": "person", "confidence": 0.88}])
    assert any(o.get("is_crawling") for o in r), "Expected is_crawling=True after sustained flat aspect"


def test_slow_loitering_flag():
    tr = MultiObjectTracker(max_disappeared=40, iou_threshold=0.2)
    # Person almost stationary for many frames
    for i in range(20):
        # tiny jitter < 2 px
        x = 100 + (i % 2) * 0.5
        r = tr.update([{"bbox": [x, 100, x + 40, 180], "label": "person", "confidence": 0.9}])
    assert any(o.get("is_slow_loitering") for o in r), "Expected is_slow_loitering for near-zero velocity"
