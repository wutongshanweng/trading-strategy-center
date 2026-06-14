"""WebSocket endpoints for real-time trading data streaming."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Optional
import asyncio
import json
from datetime import datetime

from api.websocket.manager import ConnectionManager
from simulation.sim_engine import SimEngine

router = APIRouter()
manager = ConnectionManager()
_engine = SimEngine()


@router.websocket("/ws/trading/{channel}")
async def trading_websocket(ws: WebSocket, channel: str = "default"):
    """WebSocket endpoint for real-time trading data.

    Channels:
    - positions: Real-time position updates
    - market: Market data stream
    - alerts: Alert notifications
    - all: All data streams
    """
    await manager.connect(ws, channel)
    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            action = msg.get("action", "")

            if action == "subscribe":
                await manager.send_personal(ws, {
                    "type": "subscribed",
                    "channel": channel,
                    "timestamp": datetime.now().isoformat(),
                })
            elif action == "positions":
                positions = _engine.positions.get_all()
                await manager.send_personal(ws, {
                    "type": "positions",
                    "data": [
                        {
                            "symbol": p.symbol,
                            "direction": p.direction.value,
                            "quantity": p.quantity,
                            "entry_price": p.entry_price,
                            "current_price": p.current_price,
                            "pnl": p.pnl,
                        }
                        for p in positions
                    ],
                    "timestamp": datetime.now().isoformat(),
                })
            elif action == "summary":
                summary = _engine.get_portfolio_summary()
                await manager.send_personal(ws, {
                    "type": "summary",
                    "data": summary,
                    "timestamp": datetime.now().isoformat(),
                })
            elif action == "ping":
                await manager.send_personal(ws, {"type": "pong"})
    except WebSocketDisconnect:
        await manager.disconnect(ws, channel)
    except Exception as e:
        await manager.disconnect(ws, channel)


async def broadcast_positions():
    """Broadcast current positions to all connected clients."""
    positions = _engine.positions.get_all()
    data = {
        "type": "positions_update",
        "data": [
            {
                "symbol": p.symbol,
                "direction": p.direction.value,
                "quantity": p.quantity,
                "entry_price": p.entry_price,
                "current_price": p.current_price,
                "pnl": p.pnl,
            }
            for p in positions
        ],
        "timestamp": datetime.now().isoformat(),
    }
    await manager.broadcast(data, channel="positions")


async def broadcast_summary():
    """Broadcast portfolio summary to all connected clients."""
    summary = _engine.get_portfolio_summary()
    data = {
        "type": "summary_update",
        "data": summary,
        "timestamp": datetime.now().isoformat(),
    }
    await manager.broadcast(data, channel="all")


def start_periodic_updates(interval: int = 5):
    """Start periodic broadcast of trading data."""
    async def _data_generator():
        return {
            "type": "periodic_update",
            "positions": [
                {
                    "symbol": p.symbol,
                    "direction": p.direction.value,
                    "quantity": p.quantity,
                    "entry_price": p.entry_price,
                    "current_price": p.current_price,
                    "pnl": p.pnl,
                }
                for p in _engine.positions.get_all()
            ],
            "summary": _engine.get_portfolio_summary(),
            "timestamp": datetime.now().isoformat(),
        }
    manager.start_periodic_broadcast(interval, _data_generator)
