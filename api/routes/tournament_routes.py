"""API routes for Strategy Tournament — rankings, scoring, and elimination."""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional
from tournament.tournament_manager import TournamentManager

router = APIRouter(prefix="/api/v1/tournament", tags=["tournament"])
_manager = TournamentManager()


class RegisterRequest(BaseModel):
    name: str


class RecordTradeRequest(BaseModel):
    name: str
    pnl: float


class EliminationResponse(BaseModel):
    message: str
    eliminated: int
    remaining: int


class LeaderboardEntry(BaseModel):
    rank: int
    strategy_name: str
    score: float
    sharpe: float
    win_rate: float
    profit_factor: float
    max_drawdown: float
    total_return: float
    trades: int


@router.get("/standings")
async def get_standings(top_n: int = Query(default=10, ge=1, le=100)):
    """Get tournament leaderboard."""
    entries = await _manager.get_leaderboard(top_n)
    return [
        LeaderboardEntry(
            rank=e.rank,
            strategy_name=e.name,
            score=e.current_score,
            sharpe=e.sharpe,
            win_rate=e.win_rate,
            profit_factor=e.profit_factor if e.profit_factor != float("inf") else 0.0,
            max_drawdown=e.max_drawdown,
            total_return=sum(e.pnls) if e.pnls else 0.0,
            trades=e.trades,
        )
        for e in entries
    ]


@router.post("/register")
async def register_strategy(req: RegisterRequest):
    """Register a strategy for the tournament."""
    await _manager.register_strategy(req.name)
    return {"status": "registered", "name": req.name}


@router.post("/trade")
async def record_trade(req: RecordTradeRequest):
    """Record a trade result for a strategy."""
    await _manager.register_strategy(req.name)
    await _manager.record_trade(req.name, req.pnl)
    leaderboard = await _manager.get_leaderboard(100)
    entry = next((e for e in leaderboard if e.name == req.name), None)
    return {"status": "recorded", "name": req.name, "trades": entry.trades if entry else 0}


@router.post("/update-scores")
async def update_scores():
    """Recalculate all scores."""
    await _manager.update_scores()
    return {"status": "scores_updated"}


@router.post("/eliminate")
async def eliminate_bottom(pct: float = Query(default=0.1, ge=0.01, le=0.5)):
    """Eliminate the bottom percentage of strategies."""
    before = len(_manager._entries)
    await _manager.eliminate_bottom(pct)
    after = len(_manager._entries)
    return EliminationResponse(
        message=f"Eliminated {before - after} strategies",
        eliminated=before - after,
        remaining=after,
    )


@router.get("/summary")
async def tournament_summary():
    """Get tournament summary statistics."""
    summary = await _manager.get_tournament_summary()
    return summary
