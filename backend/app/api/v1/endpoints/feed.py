"""
WebSocket live-feed endpoint.

Architecture:
  worker.py  →  Redis pub/sub channel "aegis:feed"
  FastAPI WS →  subscribes to the channel, fans out to all connected browsers

Each message published is a JSON string (the processed log_entry dict).
"""
import logging

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError

from app.core.config import settings
from app.core.security import decode_token

router = APIRouter()
logger = logging.getLogger(__name__)

PUBSUB_CHANNEL = "aegis:feed"


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        logger.info(f"WS client connected. Total: {len(self.active)}")

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)
        logger.info(f"WS client disconnected. Total: {len(self.active)}")

    async def broadcast(self, message: str):
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)


manager = ConnectionManager()


@router.websocket("/ws/feed")
async def websocket_feed(
    websocket: WebSocket,
    token: str | None = Query(default=None),
):
    """
    Browser clients connect to /api/v1/ws/feed?token=<JWT>.
    They receive every processed log entry as a JSON string in real-time.
    """
    # Validate JWT before accepting
    if not token:
        await websocket.close(code=4401, reason="Missing token")
        return
    try:
        payload = decode_token(token)
        if not payload.get("sub"):
            raise ValueError("no sub")
    except (JWTError, ValueError):
        await websocket.close(code=4401, reason="Invalid token")
        return

    await manager.connect(websocket)

    # Each WS connection gets its own async Redis subscription
    r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe(PUBSUB_CHANNEL)

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"])
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WS feed error: {e}")
    finally:
        manager.disconnect(websocket)
        await pubsub.unsubscribe(PUBSUB_CHANNEL)
        await r.aclose()
