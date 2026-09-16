#!/usr/bin/env python3
"""
Loop a local video file as if it were a camera feed (OpenCV).

Use with edge config:
  cameras:
    - camera_id: "BOP-001-CAM-01"
      source: "path/to/border_demo.mp4"   # or 0 for webcam
      enabled: true

Examples:
  python scripts/rtsp_simulator.py --video samples/border_demo.mp4 --preview
  python scripts/rtsp_simulator.py --video demo.mp4 --fps 15 --max-frames 300
"""
from __future__ import annotations

import argparse
import sys
import time


def main() -> int:
    ap = argparse.ArgumentParser(description="Loop video as offline camera source helper")
    ap.add_argument("--video", required=True, help="Path to mp4/avi demo clip")
    ap.add_argument("--fps", type=float, default=15.0)
    ap.add_argument("--preview", action="store_true", help="Show OpenCV window")
    ap.add_argument("--max-frames", type=int, default=0, help="0 = infinite loop")
    ap.add_argument("--print-edge-yaml", action="store_true")
    args = ap.parse_args()

    try:
        import cv2
    except ImportError:
        print("OpenCV required: pip install opencv-python", file=sys.stderr)
        return 1

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"Cannot open video: {args.video}", file=sys.stderr)
        return 1

    if args.print_edge_yaml:
        print(
            f'''# Paste into configs/edge_config.yaml
cameras:
  - camera_id: "BOP-001-CAM-01"
    source: "{args.video}"
    enabled: true
'''
        )

    print(
        "Simulator OK. Point Edge `source` to this file path for offline demo.\n"
        "Optional multi-stream: MediaMTX/go2rtc; Edge can use file path without extra servers."
    )

    delay = 1.0 / max(args.fps, 1.0)
    n = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        n += 1
        if args.preview:
            cv2.imshow("IBVAP offline camera sim", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        else:
            time.sleep(delay)
        if args.max_frames and n >= args.max_frames:
            break

    cap.release()
    if args.preview:
        cv2.destroyAllWindows()
    print(f"Frames played: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
