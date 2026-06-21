"""交易信号提醒 API — 活跃信号列表 / 单信号全链路详情 / 手动刷新。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("")
async def list_alerts(limit: int = Query(20, le=100)):
    """当前活跃信号列表。"""
    from signals.alert_aggregator import get_aggregator
    return get_aggregator().get_active(limit=limit)


@router.post("/refresh")
async def refresh_alerts():
    """手动触发一次全扫描。"""
    from signals.alert_aggregator import get_aggregator
    signals = get_aggregator().run_once()
    return {"refreshed": True, "count": len(signals)}


@router.get("/{sig_id}")
async def get_alert(sig_id: str):
    """单个信号全链路详情。"""
    from signals.alert_aggregator import get_aggregator
    detail = get_aggregator().get_by_id(sig_id)
    if detail is None:
        raise HTTPException(404, f"信号不存在: {sig_id}")
    return detail
