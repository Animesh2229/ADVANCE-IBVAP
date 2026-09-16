# IBVAP Evaluation Brief (1 page)

**Build:** defense/jury-upgrades-v1.3.2+
**Command:** `python scripts/eval_metrics.py --gallery-size 500`

## Synthetic micro-benchmarks
- Face gallery match latency: see JSON `face_match.ms_per_query`
- Tracker ms/frame: see JSON `tracker.ms_per_frame`

## Illustrative condition priors (not field certification)

| Condition | Det mAP50 | Face TPR | ANPR |
|-----------|-----------|----------|------|
| Day clear | 0.91 | 0.89 | 0.94 |
| Night / low light | 0.68 | 0.61 | 0.72 |
| Fog / dust / rain | 0.55 | 0.48 | 0.60 |

## Honesty
Replace priors with **labeled BOP footage** before operational accuracy claims.
Mitigations: night enhance, per-BOP thresholds, human-in-loop on HIGH.

## Hardware path
`python scripts/export_onnx_trt.py --trt-notes` — ONNX / TensorRT / OpenVINO options for low-end posts.
