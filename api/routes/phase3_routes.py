"""
Phase 3 API — ML 特征 + 期权深度 (曲面/套利/联合策略) 演示接口。

均为只读/无状态计算, 用合成或传入数据, 供前端展示。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/phase3", tags=["phase3"])


def _safe(v) -> float:
    try:
        f = float(v)
        return f if np.isfinite(f) else 0.0
    except (TypeError, ValueError):
        return 0.0


@router.get("/ml/features")
async def ml_features() -> Dict[str, Any]:
    """列出 ML 技术面特征集 (名称/分类)。"""
    from ml.features.pipeline import FeaturePipeline
    from ml.features.technical_features import TechnicalFeatureSet
    pipe = FeaturePipeline()
    pipe.register_module(TechnicalFeatureSet())
    feats = pipe.list_features()
    return {"success": True, "count": len(feats), "features": feats}


class SurfaceRequest(BaseModel):
    forward: float = 100.0
    n_strikes: int = 15
    n_ttm: int = 8
    # 可选: 自定义切片 {T: {"strikes":[...], "ivs":[...]}}
    slices: Optional[Dict[str, Dict[str, List[float]]]] = None


@router.post("/options/surface")
async def options_surface(req: SurfaceRequest) -> Dict[str, Any]:
    """构建波动率曲面并返回网格 (用于前端 3D/热力图) + 偏度/曲率/期限结构。"""
    try:
        from options.volatility.surface import VolSurface
        surface = VolSurface()
        surface.set_forward(req.forward)
        if req.slices:
            for t_str, sl in req.slices.items():
                surface.add_slice(float(t_str),
                                  np.asarray(sl["strikes"], dtype=float),
                                  np.asarray(sl["ivs"], dtype=float))
        else:
            # 合成带偏斜微笑曲面
            K = np.arange(req.forward * 0.8, req.forward * 1.2, req.forward * 0.05)
            for T, base in [(0.1, 0.20), (0.3, 0.22), (0.6, 0.25)]:
                surface.add_slice(T, K, base + 0.003 * (req.forward - K))
        surface.build()

        T_grid, K_grid, IV_grid = surface.surface_to_grid(req.n_strikes, req.n_ttm)
        if IV_grid is None:
            raise HTTPException(422, "曲面构建失败 (切片不足)")

        # 网格转 list, NaN→null 友好
        grid = [[None if (v is None or not np.isfinite(v)) else round(float(v), 4)
                 for v in row] for row in IV_grid]
        Ts = sorted(surface.slices.keys())
        term = [{"T": _safe(t), "iv": _safe(iv)}
                for t, iv in surface.get_term_structure(req.forward)]
        return {
            "success": True,
            "forward": req.forward,
            "strikes": [round(float(k), 2) for k in K_grid[:, 0]],
            "ttms": [round(float(t), 3) for t in T_grid[0, :]],
            "iv_grid": grid,
            "skew": {str(round(t, 2)): _safe(surface.get_skew(t)) for t in Ts},
            "curvature": {str(round(t, 2)): _safe(surface.get_curvature(t)) for t in Ts},
            "term_structure": term,
        }
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"曲面构建失败: {str(e)}")


@router.post("/options/arbitrage")
async def options_arbitrage(req: SurfaceRequest) -> Dict[str, Any]:
    """基于波动率曲面计算期限结构套利信号。"""
    try:
        from options.volatility.surface import VolSurface
        from options.strategies.term_arbitrage import TermArbitrageSignals
        surface = VolSurface()
        surface.set_forward(req.forward)
        K = np.arange(req.forward * 0.8, req.forward * 1.2, req.forward * 0.05)
        for T, base in [(0.1, 0.20), (0.3, 0.22), (0.6, 0.25)]:
            surface.add_slice(T, K, base + 0.005 * (req.forward - K))
        surface.build()
        sigs = TermArbitrageSignals().compute(surface, spot=req.forward)
        return {"success": True, "count": len(sigs), "signals": [
            {"type": s.signal_type, "direction": s.direction,
             "score": _safe(s.score), "confidence": _safe(s.confidence),
             "reason": s.reason, "suggested_strategy": s.suggested_strategy}
            for s in sigs]}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"套利信号计算失败: {str(e)}")


class ComboRequest(BaseModel):
    futures_direction: str = "BUY"
    futures_confidence: float = 0.7
    iv_rank: float = 50.0
    skew: float = 0.0
    spot: float = 100.0


@router.post("/options/combo")
async def options_combo(req: ComboRequest) -> Dict[str, Any]:
    """期权-期货联合策略决策。"""
    try:
        from options.strategies.futures_combo import FuturesOptionsComboSignals
        sig = FuturesOptionsComboSignals().combine(
            req.futures_direction, req.futures_confidence,
            req.iv_rank, req.skew, req.spot)
        return {"success": True, "advice": {
            "strategy_name": sig.strategy_name,
            "futures_direction": sig.futures_direction,
            "options_leg": sig.options_leg,
            "adjusted_confidence": _safe(sig.adjusted_confidence),
            "adjusted_direction": sig.adjusted_direction,
            "reason": sig.reason, "risk_notes": sig.risk_notes}}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"联合策略计算失败: {str(e)}")
