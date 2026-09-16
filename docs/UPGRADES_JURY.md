# Jury-Impact Upgrades (v1.3.x → production-ready deltas)

Implemented for maximum SIH jury impact:

## 1. Suspicious Behavior Core (edge)
- Aspect-ratio dynamics in KalmanBoxTracker → is_crawling → CRAWLING (HIGH)
- Velocity thresholding → is_slow_loitering → SUSPICIOUS_LOITERING
- Files: edge/ai_pipeline/tracker.py, pipeline.py, edge/decision/alert_engine.py

## 2. Storage-Aware Offline Queue
- shutil.disk_usage monitor; free < 10% → prune LOW/MEDIUM first
- Dynamic payload: drop snapshots after repeated network failures
- Files: edge/decision/alert_engine.py

## 3. Predictive Multi-Camera Fusion
- HSV color histogram on edge (appearance.py)
- Fusion: face → plate → color hist + 30s window + optional topology
- Files: central/services/fusion.py, edge/ai_pipeline/appearance.py

## 4. Network Resilience
- Exponential backoff with full jitter
- Fail-count driven snapshot suppression

## 5. WebRTC Live Video path
- Signaling API under /api/v1/webrtc/* (stub)
- Production: wire aiortc for real SDP answer

## Languages
- Dashboard + Field app: en / hi / ne / dz

## Tests
```bash
cd edge && PYTHONPATH=. pytest tests/ -v
cd ../central && PYTHONPATH=. pytest tests/ -v
```
