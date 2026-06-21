"""模拟交易 API — 持仓 / 开平仓 / 历史 / 关注列表 / 实时行情。"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["simulated-trading"])


class OpenRequest(BaseModel):
    symbol: str
    direction: str               # long / short
    price: float
    qty: int
    stop_loss: float = 0.0
    take_profit: float = 0.0


class CloseRequest(BaseModel):
    close_price: Optional[float] = None


class WatchAddRequest(BaseModel):
    signal: dict


# ---- 实时行情 ----
@router.get("/market/realtime")
async def market_realtime(symbols: str = Query(..., description="逗号分隔合约号")):
    """实时行情快照。"""
    from data_center.realtime_quote import get_realtime
    contracts: List[str] = [s for s in symbols.split(",") if s.strip()]
    return get_realtime(contracts)


# ---- 持仓 ----
@router.get("/simulated/positions")
async def positions():
    from simulation.simulated_trading import get_service
    return get_service().list_positions()


@router.post("/simulated/open")
async def open_position(req: OpenRequest):
    from simulation.simulated_trading import get_service
    return get_service().open_position(
        symbol=req.symbol, direction=req.direction, price=req.price,
        qty=req.qty, stop_loss=req.stop_loss, take_profit=req.take_profit)


@router.post("/simulated/close/{pos_id}")
async def close_position(pos_id: str, req: CloseRequest):
    from simulation.simulated_trading import get_service
    try:
        return get_service().close_position(pos_id, close_price=req.close_price)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/simulated/history")
async def history():
    from simulation.simulated_trading import get_service
    return get_service().history()


# ---- 关注列表 ----
@router.get("/simulated/watchlist")
async def watchlist():
    from simulation.simulated_trading import get_service
    return get_service().list_watchlist()


@router.post("/simulated/watchlist/add")
async def watchlist_add(req: WatchAddRequest):
    from simulation.simulated_trading import get_service
    return get_service().add_watchlist(req.signal)


@router.post("/simulated/watchlist/remove")
async def watchlist_remove(sig_id: str = Query(...)):
    from simulation.simulated_trading import get_service
    return get_service().remove_watchlist(sig_id)
