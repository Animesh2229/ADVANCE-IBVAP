"""
Minimal WebRTC signaling stub for low-latency live video (jury demo path).

Full pipeline:
  1. Dashboard creates RTCPeerConnection
  2. POSTs SDP offer to /api/v1/webrtc/offer
  3. Central (or edge proxy) returns SDP answer
  4. ICE candidates exchanged via /api/v1/webrtc/ice

For production: use aiortc on edge/central and replace this in-memory store
with Redis-backed rooms. Install: pip install aiortc av

This stub keeps the API contract stable so the React client can be built now.
"""
from __future__ import annotations

import time
import uuid
from typing import Dict, Any, Optional

# room_id -> {offer, answer, candidates, created_at}
_rooms: Dict[str, Dict[str, Any]] = {}
_ROOM_TTL = 600  # seconds


def _purge():
    now = time.time()
    dead = [k for k, v in _rooms.items() if now - v.get("created_at", 0) > _ROOM_TTL]
    for k in dead:
        _rooms.pop(k, None)


def create_room(camera_id: str, offer_sdp: str) -> dict:
    _purge()
    room_id = str(uuid.uuid4())[:12]
    _rooms[room_id] = {
        "camera_id": camera_id,
        "offer": offer_sdp,
        "answer": None,
        "candidates": [],
        "created_at": time.time(),
    }
    return {
        "room_id": room_id,
        "camera_id": camera_id,
        "status": "waiting_answer",
        "note": "Wire aiortc on edge to produce real SDP answer for production.",
    }


def set_answer(room_id: str, answer_sdp: str) -> Optional[dict]:
    room = _rooms.get(room_id)
    if not room:
        return None
    room["answer"] = answer_sdp
    return {"room_id": room_id, "status": "connected"}


def add_ice(room_id: str, candidate: dict) -> bool:
    room = _rooms.get(room_id)
    if not room:
        return False
    room["candidates"].append(candidate)
    return True


def get_room(room_id: str) -> Optional[dict]:
    return _rooms.get(room_id)
