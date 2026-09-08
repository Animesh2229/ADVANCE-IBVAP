from services.pii_redact import redact, safe_log_dict


def test_redact_plate_and_embedding():
    raw = {
        "camera_id": "BOP-1",
        "plate": "UK07AB1234",
        "embedding": [0.1] * 128,
        "nested": {"snapshot": "base64longvaluehere"},
    }
    out = safe_log_dict(raw)
    assert out["camera_id"] == "BOP-1"
    assert "UK07AB1234" not in str(out.get("plate", ""))
    emb = str(out.get("embedding", "")).lower()
    assert "redacted" in emb or "vector" in emb
    snap = str(out["nested"]["snapshot"])
    assert "base64longvaluehere" not in snap
    assert "***" in snap or "redacted" in snap.lower()


def test_redact_preserves_safe_fields():
    raw = {"priority": "HIGH", "alert_type": "INTRUSION", "confidence": 0.9}
    assert redact(raw) == raw
