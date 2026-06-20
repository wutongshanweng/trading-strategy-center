"""
ML + 期权 一键分析 API (Phase4 E篇)。

输入合约代码 → ML 预测结论 + 期权分析结论 + 联合策略建议。

- ML: 仓库取数 → FeaturePipeline 特征 → 即时训练轻量 rf → 预测未来 horizon 天方向
- 期权: 合成带偏斜波动率曲面 (实盘期权链在当前环境日期下拉不到, 见项目记录) →
        IV Rank/skew/期限结构/套利信号
- combo: 期货方向(来自ML) + 期权状态 → FuturesOptionsComboSignals 联合策略
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/ml-options", tags=["ml-options"])


def _safe(v) -> float:
    try:
        f = float(v)
        return f if np.isfinite(f) else 0.0
    except (TypeError, ValueError):
        return 0.0


def _conf_label(score: float) -> str:
    a = abs(score)
    if a > 0.15:
        return "高"
    if a > 0.08:
        return "中高"
    if a > 0.03:
        return "中"
    return "低"


class AnalysisRequest(BaseModel):
    symbol: str
    horizon: int = 5


def _ml_prediction(symbol: str, horizon: int) -> Dict[str, Any]:
    """即时训练轻量模型给方向预测; 数据不足时返回 HOLD。"""
    from core.alpha import factor_cli
    from ml.features.pipeline import FeaturePipeline
    from ml.features.technical_features import TechnicalFeatureSet
    from ml.models.sklearn_wrapper import SklearnModel
    from ml.model_selector import _ic

    df = factor_cli._load_from_warehouse(symbol)
    if df is None or len(df) < 80:
        return {"direction": "HOLD", "confidence": "低", "confidence_score": 0.0,
                "predicted_return": 0.0, "model_name": "n/a", "model_health": "WARNING",
                "feature_count": 0, "trained_at": "", "note": "数据不足"}

    pipe = FeaturePipeline()
    pipe.register_module(TechnicalFeatureSet())
    X = pipe.compute_all(df, dropna=True)
    y = df["close"].pct_change(horizon).shift(-horizon)
    common = X.index.intersection(y.dropna().index)
    X, y = X.loc[common], y.loc[common]
    if len(X) < 50:
        return {"direction": "HOLD", "confidence": "低", "confidence_score": 0.0,
                "predicted_return": 0.0, "model_name": "n/a", "model_health": "WARNING",
                "feature_count": int(X.shape[1]), "trained_at": "", "note": "有效样本不足"}

    split = int(len(X) * 0.8)
    Xtr, Xval = X.iloc[:split].values, X.iloc[split:].values
    ytr, yval = y.iloc[:split].values, y.iloc[split:].values
    model = SklearnModel("rf", {"n_estimators": 80, "max_depth": 6}).fit(Xtr, ytr)
    val_ic = _ic(np.asarray(model.predict(Xval)).ravel(), yval)
    # 用全量重训后预测最后一行
    model = SklearnModel("rf", {"n_estimators": 80, "max_depth": 6}).fit(X.values, y.values)
    pred_ret = float(model.predict(X.iloc[[-1]].values)[0])

    direction = "BUY" if pred_ret > 0.002 else "SELL" if pred_ret < -0.002 else "HOLD"
    health = "HEALTHY" if val_ic > 0.03 else "WARNING" if val_ic > -0.02 else "DECAYED"
    return {
        "direction": direction, "confidence": _conf_label(val_ic),
        "confidence_score": round(_safe(val_ic), 4),
        "predicted_return": round(_safe(pred_ret), 4),
        "model_name": f"rf_{symbol}", "model_health": health,
        "feature_count": int(X.shape[1]), "trained_at": str(df.index[-1])[:10],
        "val_ic": round(_safe(val_ic), 4),
    }


def _option_analysis(symbol: str, spot: float) -> Dict[str, Any]:
    """合成带偏斜曲面 → IV/skew/期限结构/套利信号。"""
    from options.volatility.surface import VolSurface
    from options.strategies.term_arbitrage import TermArbitrageSignals

    surface = VolSurface()
    surface.set_forward(spot)
    K = np.arange(spot * 0.8, spot * 1.2, spot * 0.05)
    for T, base in [(0.1, 0.20), (0.3, 0.22), (0.6, 0.25)]:
        surface.add_slice(T, K, base + 0.004 * (spot - K))
    surface.build()

    skew = _safe(surface.get_skew(0.3))
    ts = surface.get_term_structure(spot)
    term_struct = "FLAT"
    if len(ts) >= 2:
        spread = ts[-1][1] - ts[0][1]
        term_struct = "CONTANGO" if spread > 0.01 else "BACKWARD" if spread < -0.01 else "FLAT"
    # IV Rank 用近月 ATM IV 在该切片内的相对位置近似
    near = surface.slices[sorted(surface.slices)[0]]
    iv_rank = float((near.ivs.mean() - near.ivs.min()) /
                    (near.ivs.max() - near.ivs.min() + 1e-9) * 100)
    sigs = TermArbitrageSignals().compute(surface, spot=spot)
    return {
        "iv_rank": round(iv_rank, 1), "skew": round(skew, 4),
        "term_structure": term_struct,
        "arb_signals": [{"type": s.signal_type, "direction": s.direction,
                         "score": _safe(s.score), "reason": s.reason} for s in sigs],
    }


@router.post("/analyze")
async def ml_options_analyze(req: AnalysisRequest) -> Dict[str, Any]:
    """ML + 期权 一键分析。"""
    try:
        from core.alpha import factor_cli
        from options.strategies.futures_combo import FuturesOptionsComboSignals

        df = factor_cli._load_from_warehouse(req.symbol)
        if df is None or df.empty:
            raise HTTPException(404, f"{req.symbol} 无仓库数据")
        spot = float(df["close"].iloc[-1])

        ml = _ml_prediction(req.symbol, req.horizon)
        opt = _option_analysis(req.symbol, spot)

        # 联合策略: ML 方向 + 期权状态
        combo_sig = FuturesOptionsComboSignals().combine(
            futures_direction=ml["direction"],
            futures_confidence=min(abs(ml["confidence_score"]) * 5, 1.0),
            iv_rank=opt["iv_rank"], skew=opt["skew"], spot=spot)

        return {
            "success": True, "symbol": req.symbol, "spot": round(spot, 2),
            "ml_prediction": ml, "option_analysis": opt,
            "combo_advice": {
                "strategy_name": combo_sig.strategy_name,
                "direction": combo_sig.adjusted_direction,
                "reason": combo_sig.reason, "risk_notes": combo_sig.risk_notes,
            },
        }
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"ML+期权分析失败: {str(e)}")
