from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio
import concurrent.futures
from backtest.vectorized_engine import VectorizedBacktest
from signals.registry import get_strategy
from api.routes.data_routes import get_data_manager

router = APIRouter(prefix="/api/v1/backtest", tags=["backtest"])
_MAX_RESULTS = 1000
_results = []


class BacktestRequest(BaseModel):
    symbol: str
    strategy_name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_capital: float = 1_000_000.0


@router.post("/run")
async def run_backtest(req: BacktestRequest):
    strategy_cls = get_strategy(req.strategy_name)
    if strategy_cls is None:
        raise HTTPException(status_code=404, detail=f"Strategy '{req.strategy_name}' not found")
    if req.initial_capital <= 0:
        raise HTTPException(status_code=400, detail="initial_capital must be positive")
    strategy = strategy_cls()
    dm = get_data_manager()
    feed = await dm.get_data_feed(req.symbol, "1d", req.start_date, req.end_date)
    bt = VectorizedBacktest(initial_capital=req.initial_capital)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, bt.run, feed.df, strategy, req.symbol)
    _results.append(result)
    if len(_results) > _MAX_RESULTS:
        _results[:] = _results[-_MAX_RESULTS:]
    return {
        "strategy": result.strategy_name,
        "symbol": result.symbol,
        "total_return": result.total_return,
        "sharpe_ratio": result.sharpe_ratio,
        "max_drawdown": result.max_drawdown,
        "win_rate": result.win_rate,
        "total_trades": result.total_trades,
        "profit_factor": result.profit_factor,
        "equity_curve": result.equity_curve[::20],
    }


@router.get("/results")
async def list_results():
    return {"results": [
        {"strategy": r.strategy_name, "symbol": r.symbol,
         "total_return": r.total_return, "sharpe": r.sharpe_ratio}
        for r in _results[-20:]
    ]}
