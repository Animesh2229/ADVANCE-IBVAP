"""
PII / sensitive field redaction for logs and export payloads.
"""
from __future__ import annotations

from typing import Any, Dict, List, Union

SENSITIVE_KEYS = {
    "embedding",
    "embeddings",
    "face_embedding",
    "plate",
    "plate_number",
    "raw_data",
    "snapshot",
    "password",
    "hashed_password",
    "token",
    "access_token",
    "fcm_token",
}


def redact(obj: Any, depth: int = 0) -> Any:
    if depth > 8:
        return "***"
    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            if str(k).lower() in SENSITIVE_KEYS:
                if isinstance(v, list):
                    out[k] = f"<redacted list len={len(v)}>"
                elif isinstance(v, str) and len(v) > 8:
                    out[k] = v[:2] + "***" + v[-2:]
                else:
                    out[k] = "<redacted>"
            else:
                out[k] = redact(v, depth + 1)
        return out
    if isinstance(obj, list):
        if len(obj) > 32 and all(isinstance(x, (int, float)) for x in obj[:3]):
            return f"<redacted vector dim={len(obj)}>"
        return [redact(x, depth + 1) for x in obj[:50]]
    return obj


def safe_log_dict(data: dict) -> dict:
    return redact(data)  # type: ignore
