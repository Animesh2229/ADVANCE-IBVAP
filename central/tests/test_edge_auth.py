import time
import pytest
from cryptography.fernet import Fernet

from services.edge_auth import (
    encrypt_alert,
    decrypt_alert,
    sign,
    verify_signature,
    unwrap_secure_body,
)


@pytest.fixture
def keys():
    return Fernet.generate_key().decode(), "hmac-secret-for-tests-not-for-prod"


def test_roundtrip_encrypt_decrypt(keys):
    fkey, _ = keys
    alert = {"type": "FACE", "embedding": [0.1, 0.2], "plate": None, "camera_id": "BOP-0001-CAM-01"}
    token = encrypt_alert(alert, fkey)
    out = decrypt_alert(token, fkey)
    assert out["type"] == "FACE"
    assert out["embedding"] == [0.1, 0.2]
    assert out["camera_id"] == "BOP-0001-CAM-01"


def test_hmac_accepts_fresh_signature(keys):
    fkey, hkey = keys
    enc = encrypt_alert({"type": "ANPR", "plate": "UK07AB1234"}, fkey)
    ts = str(int(time.time()))
    sig = sign(enc, ts, hkey)
    assert verify_signature(enc, ts, sig, hkey)


def test_hmac_rejects_wrong_secret(keys):
    fkey, hkey = keys
    enc = encrypt_alert({"type": "X"}, fkey)
    ts = str(int(time.time()))
    sig = sign(enc, ts, hkey)
    assert not verify_signature(enc, ts, sig, "other-secret")


def test_hmac_rejects_stale_timestamp(keys):
    fkey, hkey = keys
    enc = encrypt_alert({"type": "X"}, fkey)
    ts = str(int(time.time()) - 10_000)
    sig = sign(enc, ts, hkey)
    assert not verify_signature(enc, ts, sig, hkey, max_skew=300)


def test_unwrap_ignores_plaintext_sidecar(keys):
    """Attacker cannot inject camera_id / priority next to ciphertext."""
    fkey, hkey = keys
    real = {"type": "INTRUSION", "priority": "HIGH", "camera_id": "BOP-0001-CAM-01"}
    enc = encrypt_alert(real, fkey)
    ts = str(int(time.time()))
    sig = sign(enc, ts, hkey)
    body = {
        "encrypted_payload": enc,
        "camera_id": "ATTACKER-CAM",
        "priority": "LOW",
        "alert_type": "FAKE",
    }
    payload = unwrap_secure_body(body, ts, sig, fkey, hkey)
    assert payload["camera_id"] == "BOP-0001-CAM-01"
    assert payload["priority"] == "HIGH"
    assert payload["type"] == "INTRUSION"


def test_unwrap_rejects_missing_hmac(keys):
    fkey, hkey = keys
    enc = encrypt_alert({"type": "X"}, fkey)
    with pytest.raises(ValueError):
        unwrap_secure_body({"encrypted_payload": enc}, str(int(time.time())), None, fkey, hkey)
