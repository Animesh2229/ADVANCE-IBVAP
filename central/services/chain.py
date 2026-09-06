"""
Lightweight immutable event chain (hash-linked log).

Theme: Blockchain & Cybersecurity (hash chain, not a full distributed ledger).

Operations:
- append_event: O(1) append with SHA-256 over (payload + prev_hash)
- verify_chain: O(E) full integrity scan
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict


def _compute_hash(event_type: str, data: dict, source: str, prev_hash: str, ts: str) -> str:
    payload = {
        "event_type": event_type,
        "data": data,
        "source": source,
        "prev_hash": prev_hash,
        "ts": ts,
    }
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


async def append_event(db, event_type: str, data: dict, source: str = "edge") -> str:
    from sqlalchemy import select
    from db.models import ImmutableEvent

    result = await db.execute(select(ImmutableEvent).order_by(ImmutableEvent.id.desc()).limit(1))
    prev = result.scalar_one_or_none()
    prev_hash = prev.hash if prev else "GENESIS"
    ts = datetime.now(timezone.utc).isoformat()
    event_hash = _compute_hash(event_type, data, source, prev_hash, ts)
    row = ImmutableEvent(
        event_type=event_type,
        data={**data, "_chain_ts": ts},
        source=source,
        prev_hash=prev_hash,
        hash=event_hash,
        signature=event_hash[:32],
    )
    db.add(row)
    return event_hash


async def verify_chain(db, limit: int = 5000) -> Dict[str, Any]:
    from sqlalchemy import select
    from db.models import ImmutableEvent

    result = await db.execute(select(ImmutableEvent).order_by(ImmutableEvent.id.asc()).limit(limit))
    rows = list(result.scalars().all())
    if not rows:
        return {"ok": True, "checked": 0, "first_break_id": None, "message": "empty chain"}

    prev_hash = "GENESIS"
    checked = 0
    for row in rows:
        data = dict(row.data or {})
        ts = data.pop("_chain_ts", None)
        if not ts:
            if row.prev_hash != prev_hash and checked > 0:
                return {
                    "ok": False,
                    "checked": checked,
                    "first_break_id": row.id,
                    "message": f"prev_hash link broken at id={row.id}",
                }
            prev_hash = row.hash
            checked += 1
            continue
        expected = _compute_hash(row.event_type, data, row.source or "edge", row.prev_hash, ts)
        if row.prev_hash != prev_hash and checked > 0:
            return {
                "ok": False,
                "checked": checked,
                "first_break_id": row.id,
                "message": f"prev_hash link broken at id={row.id}",
            }
        if expected != row.hash:
            return {
                "ok": False,
                "checked": checked,
                "first_break_id": row.id,
                "message": f"hash mismatch at id={row.id}",
            }
        prev_hash = row.hash
        checked += 1
    return {"ok": True, "checked": checked, "first_break_id": None, "message": "chain intact"}
