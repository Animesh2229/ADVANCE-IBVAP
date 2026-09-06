#!/usr/bin/env python3
"""Offline accuracy / complexity report scaffold for IBVAP."""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "central"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "edge"))

import numpy as np


def bench_face(gallery_size: int, dim: int = 512, queries: int = 50):
    from services.face_match import best_match
    gallery = [(i, f"p{i}", np.random.randn(dim).astype(float).tolist()) for i in range(gallery_size)]
    t0 = time.perf_counter()
    hits = 0
    for _ in range(queries):
        q = gallery[random.randint(0, gallery_size - 1)][2]
        q = (np.array(q) + np.random.randn(dim) * 0.01).tolist()
        m = best_match(q, gallery, threshold=0.3)
        if m:
            hits += 1
    dt = time.perf_counter() - t0
    return {
        "gallery_size": gallery_size,
        "queries": queries,
        "hit_rate_synthetic": hits / queries,
        "total_seconds": round(dt, 4),
        "ms_per_query": round(1000 * dt / queries, 3),
        "complexity": "O(G*D) vectorized matrix-vector",
    }


def bench_tracker(frames: int = 30, dets_per_frame: int = 15):
    from ai_pipeline.tracker import MultiObjectTracker
    tr = MultiObjectTracker(max_disappeared=10, iou_threshold=0.3)
    t0 = time.perf_counter()
    for f in range(frames):
        dets = []
        for i in range(dets_per_frame):
            x = 50 + i * 40 + random.randint(-5, 5)
            y = 50 + (f % 5) * 3
            dets.append({"bbox": [x, y, x + 30, y + 60], "label": "person", "confidence": 0.9})
        tr.update(dets)
    dt = time.perf_counter() - t0
    return {
        "frames": frames,
        "dets_per_frame": dets_per_frame,
        "total_seconds": round(dt, 4),
        "ms_per_frame": round(1000 * dt / frames, 3),
        "active_tracks": len(tr.trackers),
        "complexity": "O(N*M) IoU + Kalman O(1) per track",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gallery-size", type=int, default=500)
    ap.add_argument("--detections", type=int, default=15)
    ap.add_argument("--tracks-frames", type=int, default=40)
    args = ap.parse_args()
    report = {
        "note": "Synthetic micro-benchmark only. Replace with labeled datasets for real mAP/TPR/ANPR accuracy.",
        "face_match": bench_face(args.gallery_size),
        "tracker": bench_tracker(args.tracks_frames, args.detections),
        "field_metrics_template": {
            "detection_mAP50": None,
            "face_true_positive_rate": None,
            "anpr_char_accuracy": None,
            "id_switch_rate": None,
        },
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
