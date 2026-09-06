"""
Edge Alert Engine
- Builds alerts from pipeline (detections, fence, suspicious, FACE, ANPR)
- Fernet-encrypts the full alert (including embedding / plate)
- HMAC-signs the ciphertext
- Offline disk queue when Central is unreachable
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests

from .edge_auth import encrypt_alert, load_secrets, sign


class AlertEngine:
    def __init__(self, central_url="http://localhost:8000/api/v1/alerts/secure", queue_dir=None):
        self.central_url = central_url
        self.session = requests.Session()
        self.fernet_key, self.hmac_secret = load_secrets()
        self.queue_dir = Path(queue_dir or os.path.join(os.path.dirname(__file__), "..", "offline_queue"))
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.max_queue = 500

    def evaluate_from_pipeline(self, result: dict) -> list:
        alerts = []
        camera_id = result.get("camera_id")
        ts = result.get("timestamp")

        for obj in result.get("tracked_objects", []):
            if obj.get("confidence", 0) < 0.55:
                continue
            alerts.append({
                "type": "DETECTION",
                "subtype": obj.get("label"),
                "track_id": obj.get("track_id"),
                "confidence": round(float(obj["confidence"]), 3),
                "bbox": obj.get("bbox"),
                "camera_id": camera_id,
                "timestamp": ts,
                "is_night": result.get("is_night", False),
                "priority": "LOW",
            })

        for intr in result.get("intrusions", []):
            alerts.append({
                "type": "INTRUSION",
                "subtype": "VIRTUAL_FENCE",
                "track_id": intr.get("track_id"),
                "confidence": intr.get("confidence"),
                "camera_id": camera_id,
                "timestamp": ts,
                "priority": "HIGH",
            })

        for sus in result.get("suspicious", []):
            alerts.append({
                "type": "SUSPICIOUS",
                "subtype": sus.get("type"),
                "track_id": sus.get("track_id"),
                "confidence": sus.get("confidence", 0.7),
                "camera_id": camera_id,
                "timestamp": ts,
                "priority": "MEDIUM",
            })

        for face in result.get("faces", []):
            alerts.append({
                "type": "FACE",
                "subtype": "FACE_DETECTED",
                "track_id": face.get("track_id"),
                "confidence": face.get("confidence", 0.8),
                "bbox": face.get("bbox"),
                "camera_id": camera_id,
                "timestamp": ts,
                "embedding": face.get("embedding"),
                "priority": "MEDIUM",
            })

        for plate in result.get("plates", []):
            alerts.append({
                "type": "ANPR",
                "subtype": plate.get("country") or "PLATE",
                "track_id": plate.get("track_id"),
                "confidence": plate.get("confidence", 0.8),
                "bbox": plate.get("bbox"),
                "camera_id": camera_id,
                "timestamp": ts,
                "plate": plate.get("plate"),
                "priority": "MEDIUM",
            })

        snap = result.get("snapshot")
        if snap:
            for al in alerts:
                if al.get("priority") in ("HIGH", "MEDIUM"):
                    al["snapshot"] = snap

        return alerts

    def create_secure_alert(self, alert: dict) -> dict:
        encrypted = encrypt_alert(alert, self.fernet_key)
        ts = str(int(time.time()))
        return {
            "encrypted_payload": encrypted,
            "camera_id": alert.get("camera_id"),
            "timestamp": ts,
            "signature": sign(encrypted, ts, self.hmac_secret),
        }

    def _auth_headers(self, secure_alert: dict) -> dict:
        ts = str(secure_alert.get("timestamp") or int(time.time()))
        enc = secure_alert["encrypted_payload"]
        return {
            "X-IBVAP-Timestamp": ts,
            "X-IBVAP-Signature": sign(enc, ts, self.hmac_secret),
            "Content-Type": "application/json",
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
                resp = self.session.post(
                    self.central_url, json=data, headers=self._auth_headers(data), timeout=5
                )
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
            resp = self.session.post(
                self.central_url,
                json=secure_alert,
                headers=self._auth_headers(secure_alert),
                timeout=5,
            )
            if resp.status_code == 200:
                print("[Edge→Central] Alert sent")
                return True
            print(f"[Edge→Central] Failed: {resp.status_code} → queue")
            self._enqueue(secure_alert)
            return False
        except Exception as e:
            print(f"[Edge→Central] No network ({e}) → offline queue")
            self._enqueue(secure_alert)
            return False
