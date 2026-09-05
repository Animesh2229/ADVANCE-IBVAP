"""Lightweight immutable event chain (hash-linked log for Blockchain & Cybersecurity theme)."""
import hashlib
import json
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import ImmutableEvent


async def append_event(db: AsyncSession, event_type: str, data: dict, source: str = "edge") -> str:
    result = await db.execute(select(ImmutableEvent).order_by(ImmutableEvent.id.desc()).limit(1))
    prev = result.scalar_one_or_none()
    prev_hash = prev.hash if prev else "GENESIS"
    payload = {
        "event_type": event_type,
        "data": data,
        "source": source,
        "prev_hash": prev_hash,
        "ts": datetime.utcnow().isoformat(),
    }
    raw = json.dumps(payload, sort_keys=True, default=str)
    event_hash = hashlib.sha256(raw.encode()).hexdigest()
    row = ImmutableEvent(
        event_type=event_type,
        data=data,
        source=source,
        prev_hash=prev_hash,
        hash=event_hash,
        signature=event_hash[:32],
    )
    db.add(row)
    return event_hash
