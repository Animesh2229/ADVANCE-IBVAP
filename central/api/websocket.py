"""
WebSocket Manager - Real-time Alert Broadcasting

Default: in-process connection list.
Optional: REDIS_URL enables pub/sub so multiple API workers share broadcasts.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import List, Optional

from fastapi import WebSocket

logger = logging.getLogger("ibvap.websocket")

REDIS_URL = os.getenv("REDIS_URL", "").strip()
WS_CHANNEL = "ibvap:ws:alerts"


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()
        self._redis = None
        self._pubsub_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info("WebSocket connected. Total: %s", len(self.active_connections))

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info("WebSocket disconnected. Total: %s", len(self.active_connections))

    async def broadcast(self, message: dict):
        data = json.dumps(message, default=str)
        dead = []
        async with self._lock:
            peers = list(self.active_connections)
        for connection in peers:
            try:
                await connection.send_text(data)
            except Exception:
                dead.append(connection)
        if dead:
            async with self._lock:
                for d in dead:
                    if d in self.active_connections:
                        self.active_connections.remove(d)
        if self._redis is not None:
            try:
                await asyncio.to_thread(self._redis.publish, WS_CHANNEL, data)
            except Exception as exc:
                logger.warning("Redis publish failed: %s", exp if False else exc)

    async def _local_only_send(self, raw: str):
        dead = []
        async with self._lock:
            peers = list(self.active_connections)
        for connection in peers:
            try:
                await connection.send_text(raw)
            except Exception:
                dead.append(connection)
        if dead:
            async with self._lock:
                for d in dead:
                    if d in self.active_connections:
                        self.active_connections.remove(d)

    async def start_redis_subscriber(self):
        if not REDIS_URL:
            return
        try:
            import redis  # type: ignore
            self._redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
            self._redis.ping()
        except Exception as exc:
            logger.warning("Redis WS bridge disabled: %s", exc)
            self._redis = None
            return

        async def _loop():
            pubsub = self._redis.pubsub()
            pubsub.subscribe(WS_CHANNEL)
            logger.info("Subscribed to Redis channel %s", WS_CHANNEL)
            while True:
                try:
                    msg = await asyncio.to_thread(pubsub.get_message, ignore_subscribe_messages=True, timeout=1.0)
                    if msg and msg.get("type") == "message":
                        await self._local_only_send(msg["data"])
                    else:
                        await asyncio.sleep(0.05)
                except asyncio.CancelledError:
                    break
                except Exception as exc:
                    logger.warning("Redis sub loop: %s", exc)
                    await asyncio.sleep(1.0)

        self._pubsub_task = asyncio.create_task(_loop())


manager = ConnectionManager()
