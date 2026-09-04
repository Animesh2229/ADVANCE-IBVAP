import requests
import time
from cryptography.fernet import Fernet
import json
import base64
import hashlib

class AlertEngine:
    def __init__(self, central_url="http://localhost:8000/api/v1/alerts/secure"):
        self.central_url = central_url
        self.session = requests.Session()
        # Simple key for prototype (in production use proper key management)
        self.key = Fernet.generate_key()
        self.fernet = Fernet(self.key)

    def evaluate_from_pipeline(self, result: dict) -> list:
        alerts = []
        for obj in result.get("tracked_objects", []):
            if obj["confidence"] < 0.55:
                continue
            alerts.append({
                "type": "DETECTION",
                "subtype": obj["label"],
                "track_id": obj["track_id"],
                "confidence": round(obj["confidence"], 3),
                "bbox": obj["bbox"],
                "camera_id": result["camera_id"],
                "timestamp": result["timestamp"],
                "is_night": result.get("is_night", False)
            })

        for intr in result.get("intrusions", []):
            alerts.append({
                "type": "INTRUSION",
                "subtype": "VIRTUAL_FENCE",
                "track_id": intr["track_id"],
                "confidence": intr["confidence"],
                "camera_id": result["camera_id"],
                "timestamp": result["timestamp"],
                "priority": "HIGH"
            })

        for sus in result.get("suspicious", []):
            alerts.append({
                "type": "SUSPICIOUS",
                "subtype": sus["type"],
                "track_id": sus.get("track_id"),
                "confidence": sus.get("confidence", 0.7),
                "camera_id": result["camera_id"],
                "timestamp": result["timestamp"],
                "priority": "MEDIUM"
            })
        return alerts

    def create_secure_alert(self, alert: dict) -> dict:
        payload = json.dumps(alert, sort_keys=True).encode()
        encrypted = self.fernet.encrypt(payload).decode()
        signature = hashlib.sha256(payload).hexdigest()
        return {
            "encrypted_payload": encrypted,
            "signature": signature,
            "camera_id": alert["camera_id"],
            "timestamp": alert["timestamp"],
            "alert_type": alert["type"],
            "priority": alert.get("priority", "LOW")
        }

    def send_to_central(self, secure_alert: dict):
        try:
            resp = self.session.post(self.central_url, json=secure_alert, timeout=5)
            if resp.status_code == 200:
                print(f"[Edge→Central] Alert sent: {secure_alert['alert_type']}")
                return True
            else:
                print(f"[Edge→Central] Failed: {resp.status_code}")
                return False
        except Exception as e:
            print(f"[Edge→Central] Connection error: {e}")
            return False
