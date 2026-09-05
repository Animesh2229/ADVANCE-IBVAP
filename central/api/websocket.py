"""
=============================================================
WebSocket Manager - Real-time Alert Broadcasting
=============================================================
Dashboard aur clients ko live alerts push karta hai.
Jab bhi naya alert aata hai, connected clients ko turant mil jata hai.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio
import logging

logger = logging.getLogger("ibvap.websocket")


class ConnectionManager:
    """
    Saare active WebSocket connections ko manage karta hai.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()   # Thread-safety ke liye

    async def connect(self, websocket: WebSocket):
        """Naya client connect hua."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Client disconnect hua."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """
        Saare connected clients ko message bhejta hai.
        Dead connections automatically remove ho jati hain.
        """
        if not self.active_connections:
            return

        data = json.dumps(message, default=str)
        dead = []

        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.send_text(data)
                except Exception:
                    dead.append(connection)

            # Dead connections hata do
            for d in dead:
                if d in self.active_connections:
                    self.active_connections.remove(d)


# Global manager instance
manager = ConnectionManager()
