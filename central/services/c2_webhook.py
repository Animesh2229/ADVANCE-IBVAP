"""
Outbound C2 webhook push.

When C2_WEBHOOK_URL is set, Central POSTs each high/medium priority alert
to the external Command & Control ingest endpoint (schema ibvap.c2.v1).

Failures are logged and never block alert acceptance.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx

C2_WEBHOOK_URL = os.getenv("C2_WEBHOOK_URL", "").strip()
C2_WEBHOOK_TIMEOUT = float(os.getenv("C2_WEBHOOK_TIMEOUT", "5"))


def build_c2_event(alert_row: Any) -> Dict[str, Any]:
    return {
        "system": "IBVAP",
        "organization": "SSB / Police II Division",
        "schema": "ibvap.c2.v1",
        "event": {
            "event_id": getattr(alert_row, "id", None),
            "camera_id": getattr(alert_row, "camera_id", None),
            "type": getattr(alert_row, "alert_type", None),
            "subtype": getattr(alert_row, "subtype", None),
            "priority": getattr(alert_row, "priority", None),
            "status": getattr(alert_row, "status", None),
            "confidence": getattr(alert_row, "confidence", None),
            "timestamp": (
                alert_row.timestamp.isoformat()
                if getattr(alert_row, "timestamp", None)
                else None
            ),
            "event_hash": getattr(alert_row, "event_hash", None),
        },
    }


async def push_alert_to_c2(alert_row: Any) -> Optional[int]:
    """POST alert to C2 webhook if configured. Returns HTTP status or None."""
    if not C2_WEBHOOK_URL:
        return None
    priority = (getattr(alert_row, "priority", None) or "").upper()
    if priority not in ("HIGH", "MEDIUM"):
        return None
    payload = build_c2_event(alert_row)
    try:
        async with httpx.AsyncClient(timeout=C2_WEBHOOK_TIMEOUT) as client:
            r = await client.post(C2_WEBHOOK_URL, json=payload)
            return r.status_code
    except Exception as exc:  # pragma: no cover
        print(f"[C2 webhook] push failed: {exc}")
        return None
