"""
Replay protection for /api/v1/alerts/secure.

After HMAC verifies, remember (timestamp, signature) for REPLAY_TTL seconds.
Duplicate submissions within the window are rejected with 409.
"""
from __future__ import annotations

import os
import threading
import time

REPLAY_TTL = int(os.getenv("ALERT_REPLAY_TTL_SECONDS", "300"))
_REDIS_URL = os.getenv("REDIS_URL", "").strip()
_redis = None
if _REDIS_URL:
    try:
        import redis  # type: ignore
        _redis = redis.Redis.from_url(_REDIS_URL, decode_responses=True)
        _redis.ping()
    except Exception as exc:  # pragma: no cover
        print(f"[replay_guard] Redis unavailable ({exc}); using memory")
        _redis = None

_seen = {}
_lock = threading.Lock()


def _key(timestamp: str, signature: str) -> str:
    return f"{timestamp}:{signature}"


def is_replay(timestamp: str, signature: str) -> bool:
    """Return True if this (ts, sig) was already accepted recently."""
    if not timestamp or not signature:
        return False
    k = _key(str(timestamp), str(signature))
    now = time.time()
    if _redis is not None:
        rkey = f"ibvap:replay:{k}"
        ok = _redis.set(rkey, "1", nx=True, ex=REPLAY_TTL)
        return ok is None or ok is False
    with _lock:
        expired = [kk for kk, exp in _seen.items() if exp <= now]
        for kk in expired:
            _seen.pop(kk, None)
        if k in _seen and _seen[k] > now:
            return True
        _seen[k] = now + REPLAY_TTL
        if len(_seen) > 50000:
            items = sorted(_seen.items(), key=lambda x: x[1])
            for kk, _ in items[: len(items) // 2]:
                _seen.pop(kk, None)
        return False
