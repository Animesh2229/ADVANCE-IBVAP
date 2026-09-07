"""Replay guard unit tests."""
import os
os.environ.pop("REDIS_URL", None)

from services.replay_guard import is_replay


def test_first_accept_second_reject():
    ts, sig = "1710000999", "sig-unique-xyz"
    assert is_replay(ts, sig) is False
    assert is_replay(ts, sig) is True


def test_different_signature_ok():
    ts = "1710001000"
    assert is_replay(ts, "sig-a-1") is False
    assert is_replay(ts, "sig-b-2") is False
