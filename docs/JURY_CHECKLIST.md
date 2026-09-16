# Jury Defense Checklist (P0–P2)

## P0 — Must work on demo day

- [ ] PostgreSQL running; `ibvap` DB + user
- [ ] `.env` with SECRET_KEY, EDGE_FERNET_KEY, EDGE_HMAC_SECRET
- [ ] `python create_admin.py` then Central on `:8000`
- [ ] Dashboard login works (`admin` / password from `.env`)
- [ ] Edge: webcam **or** video file (`source: "demo.mp4"`)
- [ ] Person crosses virtual fence → alert on dashboard
- [ ] Offline story: stop network → queue; restore → sync (or simulate)
- [ ] Branch: `defense/jury-upgrades-v1.3.2` or merged `main` with green CI
- [ ] Screenshot of **green** GitHub Actions run

## P1 — Trust builders

- [ ] `python scripts/eval_metrics.py --gallery-size 500 --conditions day_clear,night_ir_or_low_light,fog_dust_rain`
- [ ] 1-page print / PDF of condition_priors table + honesty note
- [ ] Architecture one-liner: existing CCTV → software analytics → alerts
- [ ] Watchlist: one plate or face demo if time
- [ ] Language switch EN/HI/NE/DZ on dashboard

## P2 — Impress without overclaim

- [ ] `python scripts/export_onnx_trt.py --trt-notes` output in appendix
- [ ] `python scripts/rtsp_simulator.py --video demo.mp4 --print-edge-yaml`
- [ ] Fusion: same person two cams → one `global_id` (embedding/plate/appearance)
- [ ] Honest close: pilot single-node; field metrics after labeled pilot

## Answers ready

| Question | Answer |
|----------|--------|
| Night / fog accuracy? | Illustrative priors in eval_metrics; not certified; pilot labels next |
| Live multi-cam video? | Analytics on RTSP/file; full WebRTC media is phased (signaling stub) |
| Low-end BOP hardware? | yolo11n + optional ONNX/TensorRT export path |
| Offline days? | Priority offline queue + disk-aware prune |
