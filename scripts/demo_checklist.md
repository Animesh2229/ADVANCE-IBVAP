# Judge Demo Checklist (stable 1st-rank presentation)

## Before judges arrive
1. Strong secrets set in `.env`
2. Central up: `GET /health` and `GET /api/v1/readiness` OK
3. Dashboard login works; forced password change done
4. One Edge process with webcam or RTSP
5. Story clear: Edge never on public internet (VPN/localhost)

## Live flow (3–4 minutes)
1. Person/vehicle detection alert on Dashboard
2. Virtual fence intrusion → HIGH
3. Network cut → offline queue fills; restore → HIGH flushes first
4. Cover camera → CAMERA_HEALTH alert
5. Field app acknowledge (if available)

## Say explicitly
- System only alerts; jawan/officer decides action.
- Accuracy numbers only from stated labeled set.
- Cost model in configs/bom_cost.yaml — replace with quotations.

## Avoid
- 99% accuracy without dataset
- Production-cleared for all borders claim
- Long architecture monologue — show working path
