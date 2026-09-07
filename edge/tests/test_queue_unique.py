"""Offline queue filenames must not collide."""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
from cryptography.fernet import Fernet

os.environ["EDGE_FERNET_KEY"] = Fernet.generate_key().decode()
os.environ["EDGE_HMAC_SECRET"] = "test-hmac-secret-for-queue"

from decision.alert_engine import AlertEngine


def test_two_enqueues_same_ms_two_files():
    with tempfile.TemporaryDirectory() as td:
        eng = AlertEngine(queue_dir=td)
        with patch("time.time", return_value=1234567.890):
            eng._enqueue({"camera_id": "BOP-1-CAM-01", "encrypted_payload": "x", "timestamp": "1", "signature": "a"})
            eng._enqueue({"camera_id": "BOP-1-CAM-01", "encrypted_payload": "y", "timestamp": "1", "signature": "b"})
        files = list(Path(td).glob("*.json"))
        assert len(files) == 2
