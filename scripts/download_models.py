#!/usr/bin/env python3
"""
Download required AI models for IBVAP Edge.
Run this once before starting the edge pipeline.
"""
import os
import sys
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

def download_yolo():
    print("[1/2] Downloading YOLOv11n model...")
    try:
        from ultralytics import YOLO
        model = YOLO("yolo11n.pt")  # auto-downloads
        src = Path("yolo11n.pt")
        dest = MODELS_DIR / "yolo11n.pt"
        if src.exists() and not dest.exists():
            src.rename(dest)
            print(f"      Saved to {dest}")
        else:
            print("      Model already available")
        return True
    except Exception as e:
        print(f"      Failed: {e}")
        return False

def download_insightface():
    print("[2/2] Preparing InsightFace models...")
    try:
        import insightface
        from insightface.app import FaceAnalysis
        app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        app.prepare(ctx_id=-1, det_size=(640, 640))
        print("      InsightFace models ready")
        return True
    except Exception as e:
        print(f"      InsightFace optional / failed: {e}")
        print("      (OpenCV fallback will be used)")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("IBVAP Model Downloader")
    print("=" * 50)
    ok1 = download_yolo()
    ok2 = download_insightface()
    print("=" * 50)
    if ok1:
        print("✅ Core models ready. You can start the edge.")
    else:
        print("❌ YOLO download failed. Edge will not work.")
        sys.exit(1)
