"""SORT-style tracker unit tests."""
from ai_pipeline.tracker import MultiObjectTracker, _iou


def test_iou_overlap():
    assert abs(_iou([0, 0, 10, 10], [0, 0, 10, 10]) - 1.0) < 1e-6
    assert _iou([0, 0, 10, 10], [20, 20, 30, 30]) == 0.0


def test_track_persistence_across_frames():
    tr = MultiObjectTracker(max_disappeared=5, iou_threshold=0.2)
    d0 = [{"bbox": [100, 100, 140, 180], "label": "person", "confidence": 0.9}]
    r0 = tr.update(d0)
    assert len(r0) >= 1
    tid = r0[0]["track_id"]
    d1 = [{"bbox": [105, 102, 145, 182], "label": "person", "confidence": 0.91}]
    r1 = tr.update(d1)
    ids = {x["track_id"] for x in r1}
    assert tid in ids


def test_new_track_on_far_detection():
    tr = MultiObjectTracker(max_disappeared=5, iou_threshold=0.3)
    tr.update([{"bbox": [10, 10, 40, 60], "label": "person", "confidence": 0.9}])
    r = tr.update([
        {"bbox": [10, 10, 40, 60], "label": "person", "confidence": 0.9},
        {"bbox": [300, 300, 340, 360], "label": "person", "confidence": 0.9},
    ])
    assert len(r) >= 2
