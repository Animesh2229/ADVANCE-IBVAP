#!/usr/bin/env python3
"""
Export YOLOv11 weights to ONNX (and optional TensorRT engine notes).

Examples:
  python scripts/export_onnx_trt.py --weights yolo11n.pt --imgsz 640
  python scripts/export_onnx_trt.py --weights yolo11n.pt --trt-notes
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def export_onnx(weights: str, imgsz: int, out_dir: Path) -> Path:
    try:
        from ultralytics import YOLO
    except ImportError:
        print("Install ultralytics: pip install ultralytics", file=sys.stderr)
        raise SystemExit(1)
    model = YOLO(weights)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = model.export(format="onnx", imgsz=imgsz, simplify=True, dynamic=False)
    print(f"ONNX written: {path}")
    return Path(path)


def trt_notes() -> dict:
    return {
        "goal": "Lower latency on NVIDIA Jetson / GPU BOPs",
        "pipeline": [
            "1. python scripts/export_onnx_trt.py --weights yolo11n.pt",
            "2. On device with TensorRT: trtexec --onnx=yolo11n.onnx --saveEngine=yolo11n_fp16.engine --fp16",
            "3. Or ultralytics: YOLO('yolo11n.pt').export(format='engine', half=True)",
        ],
        "indicative_latency_ms": {
            "note": "Illustrative only — measure on target hardware",
            "yolo11n_pytorch_cpu": "~80-200ms/frame (depends on CPU)",
            "yolo11n_onnxruntime_cpu": "~40-120ms/frame",
            "yolo11n_tensorrt_fp16_jetson_orin_nano": "~15-35ms/frame (typical community range)",
        },
        "openvino": "For Intel NPU/CPU: model.export(format='openvino') then OpenVINO Runtime",
        "honesty": "Numbers are not field certification; re-benchmark on the BOP device.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", default="yolo11n.pt")
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--out-dir", default="artifacts/exports")
    ap.add_argument("--trt-notes", action="store_true")
    ap.add_argument("--skip-export", action="store_true")
    args = ap.parse_args()

    notes = trt_notes()
    if args.trt_notes or args.skip_export:
        print(json.dumps(notes, indent=2))
        return 0

    try:
        export_onnx(args.weights, args.imgsz, Path(args.out_dir))
    except SystemExit:
        raise
    except Exception as exc:
        print(f"Export failed ({exc}). Printing notes only.", file=sys.stderr)
        print(json.dumps(notes, indent=2))
        return 1
    print(json.dumps(notes, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
