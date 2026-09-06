# C2 / Command & Control Integration (SSB · Police II)

## 1. Pull export (on-demand)
`POST /api/v1/c2/export` (JWT required: admin / commander)

Optional body: `{ "limit": 50 }`

Returns recent HIGH/MEDIUM alerts under schema `ibvap.c2.v1`.

## 2. Outbound webhook (push)
Set environment variable:

```
C2_WEBHOOK_URL=https://your-c2.example.gov.in/ingest
C2_WEBHOOK_TIMEOUT=5
```

When configured, Central **POSTs** each HIGH/MEDIUM alert to this URL immediately after it is stored.
Payload shape:

```json
{
  "system": "IBVAP",
  "organization": "SSB / Police II Division",
  "schema": "ibvap.c2.v1",
  "event": {
    "event_id": 123,
    "camera_id": "BOP-0001-CAM-01",
    "type": "INTRUSION",
    "subtype": "VIRTUAL_FENCE",
    "priority": "HIGH",
    "status": "new",
    "confidence": 0.91,
    "timestamp": "2026-09-06T05:00:00",
    "event_hash": "..."
  }
}
```

Webhook failures are logged and **do not** reject the original edge alert.

## 3. Health
`GET /health` includes `"c2_webhook_configured": true|false`.
