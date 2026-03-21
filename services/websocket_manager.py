"""
services/websocket_manager.py

WebSocket broadcast manager with optional Redis pub/sub backend.

If REDIS_URL is set in environment:
  - Uses Redis pub/sub so broadcasts work across multiple Uvicorn workers
  - Required for production on Render with --workers > 1

If REDIS_URL is not set (local dev / single worker):
  - Falls back to in-memory list (works fine for single-worker dev)
"""
import os
import json
import asyncio
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)

REDIS_URL    = os.getenv("REDIS_URL", "").strip().strip('"').strip("'")
CHANNEL_NAME = "placement_portal_ws"


class WebSocketManager:
    def __init__(self):
        self.connections: list[WebSocket] = []
        self._redis_pub  = None
        self._redis_sub  = None
        self._redis_task = None

    async def _init_redis(self):
        """Initialise Redis clients lazily on first use."""
        if self._redis_pub is not None:
            return
        try:
            import redis.asyncio as aioredis
            self._redis_pub = await aioredis.from_url(
                REDIS_URL, encoding="utf-8", decode_responses=True
            )
            self._redis_sub = await aioredis.from_url(
                REDIS_URL, encoding="utf-8", decode_responses=True
            )
            # Subscribe and start listener task
            await self._redis_sub.subscribe(CHANNEL_NAME)
            self._redis_task = asyncio.create_task(self._redis_listener())
            logger.info("WebSocket manager: Redis pub/sub active")
        except Exception as e:
            logger.warning(f"Redis init failed, using in-memory WS: {e}")
            self._redis_pub = None

    async def _redis_listener(self):
        """Listen for Redis messages and forward to local WS connections."""
        try:
            async for message in self._redis_sub.listen():
                if message["type"] == "message":
                    await self._local_broadcast(json.loads(message["data"]))
        except Exception as e:
            logger.error(f"Redis listener error: {e}")

    async def _local_broadcast(self, data: dict):
        """Send data to all locally connected WebSockets."""
        dead = []
        for ws in self.connections:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.connections.remove(ws)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)
        if REDIS_URL:
            await self._init_redis()

    def disconnect(self, websocket: WebSocket):
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast to all connections. Uses Redis if available."""
        if REDIS_URL and self._redis_pub:
            try:
                await self._redis_pub.publish(CHANNEL_NAME, json.dumps(message))
                return
            except Exception as e:
                logger.warning(f"Redis publish failed, falling back: {e}")
        await self._local_broadcast(message)

    async def send_personal(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            self.disconnect(websocket)


ws_manager = WebSocketManager()
