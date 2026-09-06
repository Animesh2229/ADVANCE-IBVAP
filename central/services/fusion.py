"""
Multi-Camera Fusion Service (Strengthened)
Maintains global tracks across cameras using face embeddings and plates.
"""
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import uuid

class GlobalTrack:
    def __init__(self, global_id: str, label: str):
        self.global_id = global_id
        self.label = label
        self.embeddings: List[List[float]] = []
        self.plates = set()
        self.camera_history = []
        self.first_seen = datetime.now(timezone.utc)
        self.last_seen = datetime.now(timezone.utc)
        self.is_active = True

class MultiCameraFusion:
    def __init__(self, max_time_gap_seconds=180, face_threshold=0.48):
        self.global_tracks: Dict[str, GlobalTrack] = {}
        self.max_time_gap = timedelta(seconds=max_time_gap_seconds)
        self.face_threshold = face_threshold

    def _cosine_sim(self, a, b):
        a = np.array(a, dtype=np.float32)
        b = np.array(b, dtype=np.float32)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

    def update(self, camera_id: str, local_track_id: int, label: str,
               embedding: Optional[List[float]] = None,
               plate: Optional[str] = None):
        now = datetime.now(timezone.utc)
        matched_gid = None

        # Match by face embedding
        if embedding is not None:
            best_sim = -1.0
            for gid, gtrack in self.global_tracks.items():
                if not gtrack.is_active or gtrack.label != label:
                    continue
                if (now - gtrack.last_seen) > self.max_time_gap:
                    continue
                for emb in gtrack.embeddings[-5:]:
                    sim = self._cosine_sim(embedding, emb)
                    if sim > best_sim:
                        best_sim = sim
                        matched_gid = gid if best_sim >= (1 - self.face_threshold) else matched_gid

        # Match by plate
        if matched_gid is None and plate:
            for gid, gtrack in self.global_tracks.items():
                if plate in gtrack.plates and (now - gtrack.last_seen) < self.max_time_gap:
                    matched_gid = gid
                    break

        # Create new global track
        if matched_gid is None:
            matched_gid = str(uuid.uuid4())[:8]
            self.global_tracks[matched_gid] = GlobalTrack(matched_gid, label)

        gtrack = self.global_tracks[matched_gid]
        gtrack.last_seen = now
        gtrack.camera_history.append((camera_id, now.isoformat(), local_track_id))
        if embedding is not None:
            gtrack.embeddings.append(embedding)
            if len(gtrack.embeddings) > 15:
                gtrack.embeddings.pop(0)
        if plate:
            gtrack.plates.add(plate)

        return {
            "global_id": matched_gid,
            "label": label,
            "cameras_seen": list(set([c[0] for c in gtrack.camera_history])),
            "plates": list(gtrack.plates),
            "first_seen": gtrack.first_seen.isoformat(),
            "last_seen": gtrack.last_seen.isoformat()
        }

    def get_active_tracks(self, max_age_seconds=300):
        now = datetime.now(timezone.utc)
        active = {}
        for gid, gtrack in self.global_tracks.items():
            if (now - gtrack.last_seen).total_seconds() < max_age_seconds:
                active[gid] = {
                    "global_id": gid,
                    "label": gtrack.label,
                    "plates": list(gtrack.plates),
                    "cameras": list(set([c[0] for c in gtrack.camera_history[-10:]])),
                    "last_seen": gtrack.last_seen.isoformat()
                }
        return active

# Global instance
fusion_engine = MultiCameraFusion()
