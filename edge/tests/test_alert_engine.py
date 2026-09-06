import os
from cryptography.fernet import Fernet

os.environ.setdefault("EDGE_FERNET_KEY", Fernet.generate_key().decode())
os.environ.setdefault("EDGE_HMAC_SECRET", "hmac-secret-for-tests")

from decision.alert_engine import AlertEngine
from decision.edge_auth import decrypt_alert


def test_evaluate_includes_faces_and_plates():
    engine = AlertEngine(queue_dir="/tmp/ibvap-test-queue")
    result = {
        "camera_id": "BOP-0001-CAM-01",
        "timestamp": 1.0,
        "is_night": False,
        "tracked_objects": [
            {"label": "person", "confidence": 0.9, "track_id": 1, "bbox": [0, 0, 10, 10]},
        ],
        "intrusions": [],
        "suspicious": [],
        "faces": [
            {"track_id": 1, "embedding": [0.1, 0.2, 0.3], "confidence": 0.88, "bbox": [1, 1, 5, 5]},
        ],
        "plates": [
            {"track_id": 2, "plate": "UK07AB1234", "country": "IND", "confidence": 0.91},
        ],
    }
    alerts = engine.evaluate_from_pipeline(result)
    types = {a["type"] for a in alerts}
    assert "DETECTION" in types
    assert "FACE" in types
    assert "ANPR" in types
    face = next(a for a in alerts if a["type"] == "FACE")
    assert face["embedding"] == [0.1, 0.2, 0.3]
    anpr = next(a for a in alerts if a["type"] == "ANPR")
    assert anpr["plate"] == "UK07AB1234"


def test_secure_payload_embeds_face_not_plaintext_fields():
    engine = AlertEngine(queue_dir="/tmp/ibvap-test-queue")
    alert = {
        "type": "FACE",
        "camera_id": "BOP-0001-CAM-01",
        "embedding": [0.5, 0.5],
        "timestamp": 1.0,
        "priority": "MEDIUM",
    }
    secure = engine.create_secure_alert(alert)
    assert "encrypted_payload" in secure
    assert "embedding" not in secure
    inner = decrypt_alert(secure["encrypted_payload"], os.environ["EDGE_FERNET_KEY"])
    assert inner["embedding"] == [0.5, 0.5]
    assert inner["type"] == "FACE"
