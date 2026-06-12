from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from simulation.sim_engine import SimEngine
from signals.base import Direction

router = APIRouter(prefix="/api/v1/trading", tags=["trading"])
_engine = SimEngine()


class ExecuteRequest(BaseModel):
    symbol: str
    direction: str
    quantity: int = Field(default=0, gt=0)
    price: float = Field(gt=0)


@router.get("/positions")
async def list_positions():
    return {"positions": [
        {"symbol": p.symbol, "direction": p.direction.value,
         "quantity": p.quantity, "entry_price": p.entry_price,
         "current_price": p.current_price, "pnl": p.pnl}
        for p in _engine.positions.get_all()
    ]}


@router.post("/execute")
async def execute(req: ExecuteRequest):
    from signals.base import Signal
    try:
        direction = Direction(req.direction)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid direction: {req.direction}")
    signal = Signal(symbol=req.symbol, direction=direction,
                    confidence=0.5, price=req.price, strategy_name="manual")
    result = await _engine.execute_signal(signal)
    return {
        "accepted": result.accepted,
        "reason": result.reject_reason or result.reason,
        "direction": result.direction.value,
        "price": result.entry_price,
        "quantity": result.quantity,
    }


@router.post("/close/{symbol}")
async def close_position(symbol: str):
    pos = _engine.positions.get(symbol)
    if pos is None:
        raise HTTPException(status_code=404, detail=f"No open position for {symbol}")
    result = await _engine.close_position(symbol, pos.current_price)
    return {"closed": True, "symbol": symbol, "pnl": pos.pnl}


@router.get("/summary")
async def trading_summary():
    return _engine.get_portfolio_summary()
