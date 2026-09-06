"""
Per-camera rate limiter for /api/v1/alerts/secure.

Default: in-memory sliding window (single Central process).
Optional: if REDIS_URL is set and redis package is installed, use Redis
so limits survive restarts and work across multiple API workers.
"""
from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Deque, Dict, Tuple

DEFAULT_LIMIT = int(os.getenv("ALERT_RATE_LIMIT_PER_CAMERA", "30"))
DEFAULT_WINDOW = int(os.getenv("ALERT_RATE_WINDOW_SECONDS", "60"))

_REDIS_URL = os.getenv("REDIS_URL", "").strip()
_redis = None
if _REDIS_URL:
    try:
        import redis  # type: ignore

        _redis = redis.Redis.from_url(_REDIS_URL, decode_responses=True)
        _redis.ping()
    except Exception as exc:  # pragma: no cover
        print(f"[WARNING] REDIS_URL set but Redis unavailable ({exc}); using in-memory rate limit")
        _redis = None


class SlidingWindowLimiter:
    """Thread-safe sliding window counter keyed by camera_id."""

    def __init__(self, limit: int = DEFAULT_LIMIT, window_seconds: int = DEFAULT_WINDOW):
        self.limit = max(1, limit)
        self.window = max(1, window_seconds)
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> Tuple[bool, int]:
        """Return (allowed, remaining)."""
        if _redis is not None:
            return self._allow_redis(key)
        return self._allow_memory(key)

    def _allow_memory(self, key: str) -> Tuple[bool, int]:
        now = time.time()
        cutoff = now - self.window
        with self._lock:
            q = self._hits[key]
            while q and q[0] < cutoff:
                q.popleft()
            if len(q) >= self.limit:
                return False, 0
            q.append(now)
            return True, self.limit - len(q)

    def _allow_redis(self, key: str) -> Tuple[bool, int]:
        rkey = f"ibvap:rl:{key}"
        pipe = _redis.pipeline()
        pipe.incr(rkey)
        pipe.ttl(rkey)
        count, ttl = pipe.execute()
        if ttl is None or ttl < 0:
            _redis.expire(rkey, self.window)
        if int(count) > self.limit:
            return False, 0
        return True, max(0, self.limit - int(count))


alert_limiter = SlidingWindowLimiter()
