"""反馈闭环 API — 处理锦标赛结果 / 查询反馈历史与排名。"""

from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


class TournamentResults(BaseModel):
    id: str = ""
    strategies: List[Dict] = []


@router.post("/process")
async def process_results(results: TournamentResults):
    """接收锦标赛结果, 回填策略目录并生成反馈记录。"""
    from core.feedback_loop import get_feedback_loop
    entry = get_feedback_loop().process_tournament_results(results.model_dump())
    return {"success": True, "entry": entry.to_dict()}


@router.get("/history")
async def feedback_history(limit: int = 20):
    """反馈历史。"""
    from core.feedback_loop import get_feedback_loop
    return {"history": [e.to_dict() for e in get_feedback_loop().get_history(limit)]}


@router.get("/rankings")
async def strategy_rankings(min_trades: int = 0):
    """策略表现排名 (锦标赛回填后)。"""
    from core.feedback_loop import get_feedback_loop
    return {"rankings": get_feedback_loop().get_strategy_rankings(min_trades)}
