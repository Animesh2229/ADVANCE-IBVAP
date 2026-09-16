"""
Edge Alert Engine
- Builds alerts from pipeline (detections, fence, suspicious, FACE, ANPR)
- Fernet-encrypts the full alert (including embedding / plate)
- HMAC-signs the ciphertext
- Offline disk queue when Central is unreachable (UUID filenames — no overwrite)
- Storage-aware priority pruning (disk saturation safety)
- Exponential backoff + jitter on reconnect (thundering-herd protection)
"""
from __future__ import annotations

import json
import os
import random
import shutil
import time
import uuid
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
        self._fail_count = 0
        self._next_retry_at = 0.0
        self._min_free_pct = 10.0

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
            prio = "HIGH" if sus.get("type") == "CRAWLING" or sus.get("priority_hint") == "HIGH" else "MEDIUM"
            alerts.append({
                "type": "SUSPICIOUS",
                "subtype": sus.get("type"),
                "track_id": sus.get("track_id"),
                "confidence": sus.get("confidence", 0.7),
                "camera_id": camera_id,
                "timestamp": ts,
                "priority": prio,
                "aspect_ratio": sus.get("aspect_ratio"),
                "speed": sus.get("speed"),
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

    def _disk_free_pct(self) -> float:
        try:
            usage = shutil.disk_usage(self.queue_dir)
            return 100.0 * usage.free / usage.total
        except Exception:
            return 100.0

    def _priority_of_file(self, path: Path) -> str:
        meta = path.with_suffix(".meta")
        if meta.exists():
            try:
                return json.loads(meta.read_text()).get("priority", "LOW")
            except Exception:
                pass
        return "LOW"

    def _prune_if_needed(self):
        free_pct = self._disk_free_pct()
        if free_pct >= self._min_free_pct:
            return
        print(f"[Offline Queue] Disk free {free_pct:.1f}% < {self._min_free_pct}% → priority pruning")
        files = sorted(self.queue_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
        for path in files:
            prio = self._priority_of_file(path)
            if prio in ("LOW", "MEDIUM"):
                path.unlink(missing_ok=True)
                path.with_suffix(".meta").unlink(missing_ok=True)
                print(f"[Offline Queue] Pruned {path.name} ({prio})")
            if self._disk_free_pct() >= self._min_free_pct:
                break
        if self._disk_free_pct() < self._min_free_pct:
            for path in sorted(self.queue_dir.glob("*.json"), key=lambda p: p.stat().st_mtime):
                path.unlink(missing_ok=True)
                path.with_suffix(".meta").unlink(missing_ok=True)
                if self._disk_free_pct() >= self._min_free_pct:
                    break

    def _enqueue(self, secure_alert: dict, original_alert: dict = None):
        self._prune_if_needed()
        files = sorted(self.queue_dir.glob("*.json"))
        if len(files) >= self.max_queue:
            files.sort(key=lambda p: (0 if self._priority_of_file(p) == "HIGH" else 1, p.stat().st_mtime))
            files[0].unlink(missing_ok=True)
            files[0].with_suffix(".meta").unlink(missing_ok=True)
        cam = str(secure_alert.get("camera_id", "cam")).replace("/", "_")
        name = f"{int(time.time() * 1000)}_{cam}_{uuid.uuid4().hex[:10]}.json"
        path = self.queue_dir / name
        path.write_text(json.dumps(secure_alert))
        prio = (original_alert or {}).get("priority", "LOW")
        meta = {"priority": prio, "type": (original_alert or {}).get("type"), "subtype": (original_alert or {}).get("subtype")}
        path.with_suffix(".meta").write_text(json.dumps(meta))
        print(f"[Offline Queue] Saved ({len(list(self.queue_dir.glob('*.json')))} pending) prio={prio}")

    def _backoff_seconds(self) -> float:
        exp = min(self._fail_count, 6)
        base = (2 ** exp) * 0.5
        return random.uniform(0, base)

    def flush_queue(self):
        if time.time() < self._next_retry_at:
            return
        for path in sorted(self.queue_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text())
                resp = self.session.post(
                    self.central_url, json=data, headers=self._auth_headers(data), timeout=5
                )
                if resp.status_code == 200:
                    path.unlink(missing_ok=True)
                    path.with_suffix(".meta").unlink(missing_ok=True)
                    print(f"[Offline Queue] Flushed {path.name}")
                    self._fail_count = 0
                else:
                    self._fail_count += 1
                    self._next_retry_at = time.time() + self._backoff_seconds()
                    break
            except Exception:
                self._fail_count += 1
                self._next_retry_at = time.time() + self._backoff_seconds()
                break

    def send_to_central(self, secure_alert: dict, original_alert: dict = None) -> bool:
        if self._fail_count >= 3 and original_alert and "snapshot" in original_alert:
            light = {k: v for k, v in original_alert.items() if k != "snapshot"}
            secure_alert = self.create_secure_alert(light)
            original_alert = light
        if time.time() < self._next_retry_at:
            self._enqueue(secure_alert, original_alert)
            return False
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
                self._fail_count = 0
                return True
            print(f"[Edge→Central] Failed: {resp.status_code} → queue")
            self._fail_count += 1
            self._next_retry_at = time.time() + self._backoff_seconds()
            self._enqueue(secure_alert, original_alert)
            return False
        except Exception as e:
            print(f"[Edge→Central] No network ({e}) → offline queue")
            self._fail_count += 1
            self._next_retry_at = time.time() + self._backoff_seconds()
            self._enqueue(secure_alert, original_alert)
            return False
