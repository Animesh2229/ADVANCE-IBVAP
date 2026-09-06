"""
Shared Edge↔Central auth: Fernet encrypt + HMAC-SHA256 verify.

Both sides MUST use the same EDGE_FERNET_KEY and EDGE_HMAC_SECRET.
Central decrypts encrypted_payload and ignores untrusted plaintext sidecars.
"""
from __future__ import annotations

import hmac
import hashlib
import json
import os
import time
from typing import Any, Dict, Optional, Tuple

from cryptography.fernet import Fernet, InvalidToken


def load_secrets() -> Tuple[str, str]:
    fkey = os.getenv("EDGE_FERNET_KEY") or ""
    hkey = os.getenv("EDGE_HMAC_SECRET") or ""
    if not fkey or not hkey:
        raise RuntimeError(
            "EDGE_FERNET_KEY and EDGE_HMAC_SECRET must be set "
            "(generate Fernet key: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\")"
        )
    # Validate Fernet key early
    Fernet(fkey.encode() if isinstance(fkey, str) else fkey)
    return fkey, hkey


def encrypt_alert(alert: dict, fernet_key: str) -> str:
    f = Fernet(fernet_key.encode() if isinstance(fernet_key, str) else fernet_key)
    payload = json.dumps(alert, sort_keys=True, default=str).encode()
    return f.encrypt(payload).decode()


def decrypt_alert(token: str, fernet_key: str) -> dict:
    f = Fernet(fernet_key.encode() if isinstance(fernet_key, str) else fernet_key)
    raw = f.decrypt(token.encode())
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("decrypted payload is not an object")
    return data


def sign(encrypted: str, timestamp: str, hmac_secret: str) -> str:
    msg = f"{timestamp}.{encrypted}".encode()
    return hmac.new(hmac_secret.encode(), msg, hashlib.sha256).hexdigest()


def verify_signature(
    encrypted: str,
    timestamp: str,
    signature: Optional[str],
    hmac_secret: str,
    max_skew: int = 300,
) -> bool:
    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        return False
    if abs(time.time() - ts) > max_skew:
        return False
    expected = sign(encrypted, str(ts), hmac_secret)
    return hmac.compare_digest(expected, signature or "")


def unwrap_secure_body(
    body: Dict[str, Any],
    timestamp: Optional[str],
    signature: Optional[str],
    fernet_key: str,
    hmac_secret: str,
) -> dict:
    """HMAC-verify then decrypt. Raises ValueError on failure."""
    encrypted = body.get("encrypted_payload")
    if not encrypted or not isinstance(encrypted, str):
        raise ValueError("encrypted_payload required")
    if not verify_signature(encrypted, timestamp or "", signature, hmac_secret):
        raise ValueError("invalid or expired HMAC signature")
    try:
        return decrypt_alert(encrypted, fernet_key)
    except InvalidToken as exc:
        raise ValueError("cannot decrypt payload (wrong EDGE_FERNET_KEY?)") from exc
