# C2 / Command & Control Integration (SSB · Police II)

## Endpoint
`POST /api/v1/c2/export` (JWT required: admin / commander)

Optional body: `{ "limit": 50 }`

## Outbound webhook
```
C2_WEBHOOK_URL=https://your-c2.example.gov.in/ingest
```

## Schema `ibvap.c2.v1`
Fields: `event_id`, `camera_id`, `type`, `subtype`, `priority`, `status`, `confidence`, `timestamp`, `event_hash`.
