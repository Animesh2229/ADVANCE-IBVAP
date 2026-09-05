"""
Edge Alert Engine
- Builds alerts from pipeline
- Encrypts + signs
- Sends to Central; if network down → local offline queue (disk)
- Flushes queue when connectivity returns
"""
import os
import json
import time
import hashlib
from pathlib import Path

import requests
from cryptography.fernet import Fernet


class AlertEngine:
    def __init__(self, central_url="http://localhost:8000/api/v1/alerts/secure", queue_dir=None):
        self.central_url = central_url
        self.session = requests.Session()
        key = os.getenv("EDGE_FERNET_KEY")
        self.key = key.encode() if key else Fernet.generate_key()
        self.fernet = Fernet(self.key)
        self.queue_dir = Path(queue_dir or os.path.join(os.path.dirname(__file__), "..", "offline_queue"))
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.max_queue = 500

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
                "is_night": result.get("is_night", False),
            })

        for intr in result.get("intrusions", []):
            alerts.append({
                "type": "INTRUSION",
                "subtype": "VIRTUAL_FENCE",
                "track_id": intr["track_id"],
                "confidence": intr["confidence"],
                "camera_id": result["camera_id"],
                "timestamp": result["timestamp"],
                "priority": "HIGH",
            })

        for sus in result.get("suspicious", []):
            alerts.append({
                "type": "SUSPICIOUS",
                "subtype": sus["type"],
                "track_id": sus.get("track_id"),
                "confidence": sus.get("confidence", 0.7),
                "camera_id": result["camera_id"],
                "timestamp": result["timestamp"],
                "priority": "MEDIUM",
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
            "subtype": alert.get("subtype"),
            "confidence": alert.get("confidence"),
            "priority": alert.get("priority", "LOW"),
            "track_id": alert.get("track_id"),
            "bbox": alert.get("bbox"),
        }

    def _enqueue(self, secure_alert: dict):
        files = sorted(self.queue_dir.glob("*.json"))
        if len(files) >= self.max_queue:
            files[0].unlink(missing_ok=True)
        name = f"{int(time.time() * 1000)}_{secure_alert.get('camera_id', 'cam')}.json"
        path = self.queue_dir / name.replace("/", "_")
        path.write_text(json.dumps(secure_alert))
        print(f"[Offline Queue] Saved ({len(list(self.queue_dir.glob('*.json')))} pending)")

    def flush_queue(self):
        for path in sorted(self.queue_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text())
                resp = self.session.post(self.central_url, json=data, timeout=5)
                if resp.status_code == 200:
                    path.unlink(missing_ok=True)
                    print(f"[Offline Queue] Flushed {path.name}")
                else:
                    break
            except Exception:
                break

    def send_to_central(self, secure_alert: dict) -> bool:
        try:
            self.flush_queue()
            resp = self.session.post(self.central_url, json=secure_alert, timeout=5)
            if resp.status_code == 200:
                print(f"[Edge\u2192Central] Alert sent: {secure_alert.get('alert_type')}")
                return True
            print(f"[Edge\u2192Central] Failed: {resp.status_code} \u2192 queue")
            self._enqueue(secure_alert)
            return False
        except Exception as e:
            print(f"[Edge\u2192Central] No network ({e}) \u2192 offline queue")
            self._enqueue(secure_alert)
            return False
