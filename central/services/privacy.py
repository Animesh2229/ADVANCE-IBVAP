"""
Privacy controls: face embedding TTL, watchlist-only retention helpers.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

# Default: non-watchlist embeddings older than this are purged
FACE_TTL_HOURS = int(os.getenv("FACE_EMBEDDING_TTL_HOURS", "72"))


async def purge_expired_face_embeddings(db: AsyncSession, ttl_hours: Optional[int] = None) -> int:
    hours = ttl_hours if ttl_hours is not None else FACE_TTL_HOURS
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    # Only purge non-watchlist rows
    from db.models import FaceEmbedding

    result = await db.execute(
        select(FaceEmbedding).where(
            FaceEmbedding.is_watchlist == False,  # noqa: E712
            FaceEmbedding.timestamp < cutoff,
        )
    )
    rows = result.scalars().all()
    count = 0
    for row in rows:
        await db.delete(row)
        count += 1
    if count:
        await db.commit()
    return count
