from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from signals.registry import list_strategies, get_strategy
from signals.engine import StrategyEngine
from core.data.market_data_manager import MarketDataManager
from api.routes.data_routes import get_data_manager

router = APIRouter(prefix="/api/v1/strategies", tags=["strategies"])


class ComputeRequest(BaseModel):
    symbol: str
    timeframe: str = "1d"
    strategy_names: Optional[List[str]] = None


@router.get("")
async def list_all_strategies():
    return {"strategies": list_strategies()}


@router.get("/{name}")
async def get_strategy_detail(name: str):
    cls = get_strategy(name)
    if cls is None:
        raise HTTPException(status_code=404, detail=f"Strategy {name} not found")
    inst = cls()
    return {
        "name": inst.name,
        "description": inst.description,
        "timeframes": inst.timeframes,
        "params": inst.params,
    }


@router.post("/compute")
async def compute_signals(req: ComputeRequest):
    dm = get_data_manager()
    feed = await dm.get_data_feed(req.symbol, req.timeframe)
    engine = StrategyEngine()
    engine.load_all()
    signals = engine.compute_all(feed.df, req.symbol, req.strategy_names)
    return {
        "symbol": req.symbol,
        "timeframe": req.timeframe,
        "signals": [
            {
                "strategy": s.strategy_name,
                "direction": s.direction.value,
                "confidence": s.confidence,
                "price": s.price,
                "reason": s.reason,
            }
            for s in signals
        ],
        "total": len(signals),
    }
