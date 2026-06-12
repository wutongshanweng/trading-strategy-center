from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Dict
from portfolio.portfolio_manager import PortfolioManager
from simulation.sim_engine import SimEngine

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])
_pm = PortfolioManager()
_se = SimEngine()


class RebalanceRequest(BaseModel):
    target_weights: Dict[str, float]

    @field_validator("target_weights")
    @classmethod
    def check_weights(cls, v):
        if any(w < 0 for w in v.values()):
            raise ValueError("Weights must be non-negative")
        total = sum(v.values())
        if total < 0.99 or total > 1.01:
            raise ValueError(f"Weights must sum to ~1.0, got {total:.4f}")
        return v


@router.get("/stats")
async def portfolio_stats():
    return _pm.get_portfolio_stats(_se.positions.get_all())


@router.get("/correlation")
async def correlation_matrix():
    corr = _pm.correlation.compute()
    if corr.empty:
        return {"correlation": {}}
    return {"correlation": corr.to_dict()}


@router.post("/rebalance")
async def rebalance(req: RebalanceRequest):
    trades = _pm.rebalance(_se.positions.get_all(), req.target_weights)
    return {"trades": trades, "message": f"{len(trades)} rebalance trades suggested"}
