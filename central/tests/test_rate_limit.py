"""Unit tests for per-camera sliding window rate limiter."""
import os
import time

os.environ.pop("REDIS_URL", None)

from services.rate_limit import SlidingWindowLimiter


def test_allows_under_limit():
    lim = SlidingWindowLimiter(limit=3, window_seconds=60)
    ok1, rem1 = lim.allow("CAM-1")
    ok2, rem2 = lim.allow("CAM-1")
    ok3, rem3 = lim.allow("CAM-1")
    assert ok1 and ok2 and ok3
    assert rem3 == 0


def test_blocks_over_limit():
    lim = SlidingWindowLimiter(limit=2, window_seconds=60)
    assert lim.allow("CAM-A")[0] is True
    assert lim.allow("CAM-A")[0] is True
    assert lim.allow("CAM-A")[0] is False


def test_keys_are_independent():
    lim = SlidingWindowLimiter(limit=1, window_seconds=60)
    assert lim.allow("CAM-X")[0] is True
    assert lim.allow("CAM-Y")[0] is True
    assert lim.allow("CAM-X")[0] is False


def test_window_expires():
    lim = SlidingWindowLimiter(limit=1, window_seconds=1)
    assert lim.allow("CAM-Z")[0] is True
    assert lim.allow("CAM-Z")[0] is False
    time.sleep(1.1)
    assert lim.allow("CAM-Z")[0] is True
