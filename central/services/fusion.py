"""
Multi-Camera Fusion Service

Maintains global tracks across cameras using face embeddings and plates.

Persistence:
- Default: in-memory
- If FUSION_STATE_PATH is set: periodic JSON snapshot
- If REDIS_URL is set: mirror active track metadata in Redis
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import numpy as np

FUSION_STATE_PATH = os.getenv("FUSION_STATE_PATH", "").strip()
_REDIS_URL = os.getenv("REDIS_URL", "").strip()
_redis = None
if _REDIS_URL:
    try:
        import redis  # type: ignore
        _redis = redis.Redis.from_url(_REDIS_URL, decode_responses=True)
        _redis.ping()
    except Exception as exc:  # pragma: no cover
        print(f"[fusion] Redis unavailable ({exc}); memory-only")
        _redis = None


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
        self._load_state()

    def _cosine_sim(self, a, b):
        a = np.array(a, dtype=np.float32)
        b = np.array(b, dtype=np.float32)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

    def update(self, camera_id: str, local_track_id: int, label: str,
               embedding: Optional[List[float]] = None,
               plate: Optional[str] = None):
        now = datetime.now(timezone.utc)
        matched_gid = None

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

        if matched_gid is None and plate:
            for gid, gtrack in self.global_tracks.items():
                if plate in gtrack.plates and (now - gtrack.last_seen) < self.max_time_gap:
                    matched_gid = gid
                    break

        if matched_gid is None:
            matched_gid = str(uuid.uuid4())[:8]
            self.global_tracks[matched_gid] = GlobalTrack(matched_gid, label)

        gtrack = self.global_tracks[matched_gid]
        gtrack.last_seen = now
        gtrack.camera_history.append((camera_id, now.isoformat(), local_track_id))
        if len(gtrack.camera_history) > 50:
            gtrack.camera_history = gtrack.camera_history[-50:]
        if embedding is not None:
            gtrack.embeddings.append(embedding)
            if len(gtrack.embeddings) > 15:
                gtrack.embeddings.pop(0)
        if plate:
            gtrack.plates.add(plate)

        self._persist_soft()
        return {
            "global_id": matched_gid,
            "label": label,
            "cameras_seen": list(set([c[0] for c in gtrack.camera_history])),
            "plates": list(gtrack.plates),
            "first_seen": gtrack.first_seen.isoformat(),
            "last_seen": gtrack.last_seen.isoformat(),
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
                    "last_seen": gtrack.last_seen.isoformat(),
                }
        return active

    def _persist_soft(self):
        try:
            if FUSION_STATE_PATH:
                data = {}
                for gid, gt in self.global_tracks.items():
                    data[gid] = {
                        "label": gt.label,
                        "plates": list(gt.plates),
                        "embeddings": gt.embeddings[-5:],
                        "camera_history": gt.camera_history[-20:],
                        "first_seen": gt.first_seen.isoformat(),
                        "last_seen": gt.last_seen.isoformat(),
                    }
                tmp = FUSION_STATE_PATH + ".tmp"
                os.makedirs(os.path.dirname(FUSION_STATE_PATH) or ".", exist_ok=True)
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(data, f)
                os.replace(tmp, FUSION_STATE_PATH)
            if _redis is not None:
                active = self.get_active_tracks()
                _redis.setex("ibvap:fusion:active", 300, json.dumps(active))
        except Exception as exc:  # pragma: no cover
            print(f"[fusion] persist skipped: {exc}")

    def _load_state(self):
        if not FUSION_STATE_PATH or not os.path.isfile(FUSION_STATE_PATH):
            return
        try:
            with open(FUSION_STATE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for gid, row in data.items():
                gt = GlobalTrack(gid, row.get("label", "unknown"))
                gt.plates = set(row.get("plates") or [])
                gt.embeddings = row.get("embeddings") or []
                gt.camera_history = row.get("camera_history") or []
                for field, attr in (("first_seen", "first_seen"), ("last_seen", "last_seen")):
                    if row.get(field):
                        try:
                            setattr(gt, attr, datetime.fromisoformat(row[field]))
                        except Exception:
                            pass
                self.global_tracks[gid] = gt
            print(f"[fusion] restored {len(self.global_tracks)} tracks from {FUSION_STATE_PATH}")
        except Exception as exc:  # pragma: no cover
            print(f"[fusion] load failed: {exc}")


fusion_engine = MultiCameraFusion()
