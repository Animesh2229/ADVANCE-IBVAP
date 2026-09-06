"""Hash helpers for immutable chain."""
from services.chain import _compute_hash


def test_hash_deterministic():
    h1 = _compute_hash("ALERT", {"a": 1}, "edge", "GENESIS", "ts1")
    h2 = _compute_hash("ALERT", {"a": 1}, "edge", "GENESIS", "ts1")
    assert h1 == h2
    assert len(h1) == 64


def test_hash_changes_on_tamper():
    h1 = _compute_hash("ALERT", {"a": 1}, "edge", "GENESIS", "ts1")
    h2 = _compute_hash("ALERT", {"a": 2}, "edge", "GENESIS", "ts1")
    assert h1 != h2
