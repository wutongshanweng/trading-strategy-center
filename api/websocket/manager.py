import asyncio
from typing import Set, Dict, Any, Callable, Coroutine
from fastapi import WebSocket
from loguru import logger


class ConnectionManager:
    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._broadcast_task = None

    async def connect(self, ws: WebSocket, channel: str = "default"):
        await ws.accept()
        if channel not in self._connections:
            self._connections[channel] = set()
        self._connections[channel].add(ws)
        logger.info(f"WS connected: {channel} ({len(self._connections[channel])} clients)")

    async def disconnect(self, ws: WebSocket, channel: str = "default"):
        if channel in self._connections:
            self._connections[channel].discard(ws)
            if not self._connections[channel]:
                del self._connections[channel]

    async def broadcast(self, data: dict, channel: str = "default"):
        if channel not in self._connections:
            return
        dead = set()
        for ws in self._connections[channel]:
            try:
                await ws.send_json(data)
            except Exception:
                dead.add(ws)
        for ws in dead:
            await self.disconnect(ws, channel)

    async def send_personal(self, ws: WebSocket, data: dict):
        try:
            await ws.send_json(data)
        except Exception as e:
            logger.warning(f"WS send failed: {e}")

    def start_periodic_broadcast(self, interval: int, data_generator: Callable[[], Coroutine]):
        async def _loop():
            while True:
                try:
                    data = await data_generator()
                    if data:
                        await self.broadcast(data)
                except Exception as e:
                    logger.error(f"Periodic broadcast error: {e}")
                await asyncio.sleep(interval)
        self._broadcast_task = asyncio.create_task(_loop())
        logger.info(f"Periodic broadcast started every {interval}s")
