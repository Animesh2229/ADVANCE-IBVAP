import numpy as np

class MultiObjectTracker:
    def __init__(self, max_disappeared=30, max_distance=80):
        self.next_id = 1
        self.objects = {}
        self.disappeared = {}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
        self.tracks = {}

    def _centroid(self, bbox):
        x1, y1, x2, y2 = bbox
        return np.array([(x1 + x2) / 2, (y1 + y2) / 2])

    def update(self, detections: list, frame=None) -> list:
        if len(detections) == 0:
            for oid in list(self.disappeared.keys()):
                self.disappeared[oid] += 1
                if self.disappeared[oid] > self.max_disappeared:
                    self.objects.pop(oid, None)
                    self.disappeared.pop(oid, None)
                    self.tracks.pop(oid, None)
            return []

        input_centroids = np.array([self._centroid(d["bbox"]) for d in detections])

        if len(self.objects) == 0:
            for i, det in enumerate(detections):
                self._register(det, input_centroids[i])
        else:
            object_ids = list(self.objects.keys())
            object_centroids = np.array(list(self.objects.values()))

            distances = np.linalg.norm(object_centroids[:, np.newaxis] - input_centroids, axis=2)
            rows = distances.min(axis=1).argsort()
            cols = distances.argmin(axis=1)[rows]

            used_rows, used_cols = set(), set()

            for row, col in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                if distances[row, col] > self.max_distance:
                    continue

                oid = object_ids[row]
                self.objects[oid] = input_centroids[col]
                self.disappeared[oid] = 0
                self.tracks[oid].update({
                    "bbox": detections[col]["bbox"],
                    "label": detections[col]["label"],
                    "confidence": detections[col]["confidence"],
                    "centroid": input_centroids[col].tolist()
                })
                used_rows.add(row)
                used_cols.add(col)

            for col in set(range(len(detections))) - used_cols:
                self._register(detections[col], input_centroids[col])

            for row in set(range(len(object_ids))) - used_rows:
                oid = object_ids[row]
                self.disappeared[oid] += 1
                if self.disappeared[oid] > self.max_disappeared:
                    self.objects.pop(oid, None)
                    self.disappeared.pop(oid, None)
                    self.tracks.pop(oid, None)

        results = []
        for oid, info in self.tracks.items():
            results.append({
                "track_id": oid,
                "label": info["label"],
                "confidence": info["confidence"],
                "bbox": info["bbox"],
                "centroid": info["centroid"]
            })
        return results

    def _register(self, detection, centroid):
        oid = self.next_id
        self.objects[oid] = centroid
        self.disappeared[oid] = 0
        self.tracks[oid] = {
            "bbox": detection["bbox"],
            "label": detection["label"],
            "confidence": detection["confidence"],
            "centroid": centroid.tolist()
        }
        self.next_id += 1
