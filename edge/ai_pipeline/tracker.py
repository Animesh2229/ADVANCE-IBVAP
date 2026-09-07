"""
Multi-Object Tracker (SORT-style, pure NumPy)
Defensive against missing bbox/label keys.
"""
from __future__ import annotations

from typing import List
import numpy as np

try:
    from scipy.optimize import linear_sum_assignment
    _HAS_HUNGARIAN = True
except Exception:
    _HAS_HUNGARIAN = False


def _iou(b1, b2) -> float:
    x1 = max(b1[0], b2[0])
    y1 = max(b1[1], b2[1])
    x2 = min(b1[2], b2[2])
    y2 = min(b1[3], b2[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    if inter <= 0:
        return 0.0
    a1 = max(0.0, b1[2] - b1[0]) * max(0.0, b1[3] - b1[1])
    a2 = max(0.0, b2[2] - b2[0]) * max(0.0, b2[3] - b2[1])
    return float(inter / (a1 + a2 - inter + 1e-9))


def _bbox_to_z(bbox) -> np.ndarray:
    x1, y1, x2, y2 = bbox
    w = max(1.0, x2 - x1)
    h = max(1.0, y2 - y1)
    return np.array([x1 + w / 2.0, y1 + h / 2.0, w / h, h], dtype=np.float32)


def _z_to_bbox(z) -> List[float]:
    cx, cy, a, h = [float(v) for v in z[:4]]
    w = max(1.0, a * h)
    return [cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0]


class KalmanBoxTracker:
    count = 0

    def __init__(self, bbox, label: str, confidence: float):
        self.x = np.zeros((8, 1), dtype=np.float32)
        self.x[:4, 0] = _bbox_to_z(bbox)
        self.P = np.eye(8, dtype=np.float32)
        self.P[4:, 4:] *= 1000.0
        self.P *= 10.0
        self.F = np.eye(8, dtype=np.float32)
        for i in range(4):
            self.F[i, i + 4] = 1.0
        self.H = np.eye(4, 8, dtype=np.float32)
        self.R = np.eye(4, dtype=np.float32)
        self.Q = np.eye(8, dtype=np.float32)
        self.Q[4:, 4:] *= 0.01
        KalmanBoxTracker.count += 1
        self.id = KalmanBoxTracker.count
        self.label = label or "object"
        self.confidence = float(confidence or 0.5)
        self.time_since_update = 0
        self.hits = 1
        self.age = 1

    def predict(self):
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        self.age += 1
        self.time_since_update += 1
        return self.x

    def update(self, bbox, label: str, confidence: float):
        z = _bbox_to_z(bbox).reshape(4, 1)
        y = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y
        self.P = (np.eye(8, dtype=np.float32) - K @ self.H) @ self.P
        self.time_since_update = 0
        self.hits += 1
        self.label = label or self.label
        self.confidence = float(confidence or self.confidence)

    def bbox(self) -> List[float]:
        return _z_to_bbox(self.x[:, 0])


def _associate(tracks, detections, iou_threshold: float):
    if not tracks or not detections:
        return [], list(range(len(tracks))), list(range(len(detections)))
    iou_matrix = np.zeros((len(tracks), len(detections)), dtype=np.float32)
    for t, tr in enumerate(tracks):
        tb = tr.bbox()
        for d, det in enumerate(detections):
            iou_matrix[t, d] = _iou(tb, det["bbox"])
    if _HAS_HUNGARIAN:
        cost = 1.0 - iou_matrix
        row_idx, col_idx = linear_sum_assignment(cost)
        matches, unmatched_t, unmatched_d = [], set(range(len(tracks))), set(range(len(detections)))
        for r, c in zip(row_idx, col_idx):
            if iou_matrix[r, c] < iou_threshold:
                continue
            matches.append((r, c))
            unmatched_t.discard(r)
            unmatched_d.discard(c)
        return matches, list(unmatched_t), list(unmatched_d)
    matches, used_t, used_d = [], set(), set()
    pairs = [((i, j), iou_matrix[i, j]) for i in range(len(tracks)) for j in range(len(detections))]
    pairs.sort(key=lambda x: x[1], reverse=True)
    for (i, j), score in pairs:
        if score < iou_threshold:
            break
        if i in used_t or j in used_d:
            continue
        matches.append((i, j))
        used_t.add(i)
        used_d.add(j)
    return matches, [i for i in range(len(tracks)) if i not in used_t], [j for j in range(len(detections)) if j not in used_d]


class MultiObjectTracker:
    def __init__(self, max_disappeared: int = 30, max_distance: int = 80, iou_threshold: float = 0.3):
        self.max_age = max_disappeared
        self.iou_threshold = iou_threshold
        self.trackers: List[KalmanBoxTracker] = []
        self.max_distance = max_distance

    def update(self, detections: list, frame=None) -> list:
        # Defensive: drop malformed detections (missing bbox) so edge never crashes
        detections = [
            d for d in (detections or [])
            if isinstance(d, dict) and d.get("bbox") and len(d.get("bbox")) >= 4
        ]
        for tr in self.trackers:
            tr.predict()
        matches, unmatched_t, unmatched_d = _associate(self.trackers, detections, self.iou_threshold)
        for t_idx, d_idx in matches:
            det = detections[d_idx]
            self.trackers[t_idx].update(det.get("bbox") or [0, 0, 1, 1], det.get("label") or "object", float(det.get("confidence") or 0.5))
        for d_idx in unmatched_d:
            det = detections[d_idx]
            self.trackers.append(
                KalmanBoxTracker(det.get("bbox") or [0, 0, 1, 1], det.get("label") or "object", float(det.get("confidence") or 0.5))
            )
        self.trackers = [tr for tr in self.trackers if tr.time_since_update <= self.max_age]
        results = []
        for tr in self.trackers:
            if tr.time_since_update > 0 and tr.hits < 2:
                continue
            bb = tr.bbox()
            results.append({
                "track_id": tr.id,
                "label": tr.label,
                "confidence": tr.confidence,
                "bbox": bb,
                "centroid": [(bb[0] + bb[2]) / 2.0, (bb[1] + bb[3]) / 2.0],
            })
        return results
