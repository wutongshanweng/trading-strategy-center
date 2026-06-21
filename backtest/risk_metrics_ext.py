"""empyrical 风险调整收益指标扩展层 (Apache-2.0 上游)。

补全项目原有 backtest/metrics.py 之外的专业指标:
Sortino / Calmar / Omega / 信息比率 / Alpha-Beta / tail_ratio / stability / VaR。

numpy 2.0 兼容: empyrical 0.5.5 用了已移除的 np.NINF 等, 此处导入前打 shim。
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np

# ---- numpy 2.0 兼容 shim (必须在 import empyrical 之前) ----
for _name, _val in [("NINF", -np.inf), ("PINF", np.inf), ("Inf", np.inf),
                    ("NaN", np.nan), ("bool", bool), ("int", int), ("float", float),
                    ("object", object)]:
    if not hasattr(np, _name):
        setattr(np, _name, _val)

try:
    import empyrical as _ep
    _HAS_EP = True
except Exception:  # pragma: no cover
    _ep = None
    _HAS_EP = False


def _arr(returns) -> np.ndarray:
    a = np.asarray(returns, dtype=float).ravel()
    return a[np.isfinite(a)]


def _safe(fn, *args, default=0.0) -> float:
    try:
        v = float(fn(*args))
        return v if np.isfinite(v) else default
    except Exception:
        return default


def full_metrics(returns: List[float],
                 factor_returns: Optional[List[float]] = None) -> Dict:
    """对一段收益率序列计算全套风险调整指标。

    returns: 周期收益率序列 (非累计)。factor_returns: 基准收益率 (可选, 算 alpha/beta/信息比率)。
    无 empyrical 时返回 available=False。
    """
    r = _arr(returns)
    if not _HAS_EP or len(r) < 2:
        return {"available": False, "reason": "empyrical 不可用或样本不足"}

    out: Dict[str, float] = {
        "annual_return": _safe(_ep.annual_return, r),
        "annual_volatility": _safe(_ep.annual_volatility, r),
        "sharpe": _safe(_ep.sharpe_ratio, r),
        "sortino": _safe(_ep.sortino_ratio, r),
        "calmar": _safe(_ep.calmar_ratio, r),
        "omega": _safe(_ep.omega_ratio, r),
        "max_drawdown": _safe(_ep.max_drawdown, r),
        "tail_ratio": _safe(_ep.tail_ratio, r),
        "stability": _safe(_ep.stability_of_timeseries, r),
        "value_at_risk": _safe(_ep.value_at_risk, r),
        "downside_risk": _safe(_ep.downside_risk, r),
    }
    if factor_returns is not None:
        f = _arr(factor_returns)
        n = min(len(r), len(f))
        if n >= 2:
            r2, f2 = r[-n:], f[-n:]
            out["alpha"] = _safe(lambda: _ep.alpha_aligned(r2, f2))
            out["beta"] = _safe(lambda: _ep.beta_aligned(r2, f2))
            out["excess_sharpe"] = _safe(lambda: _ep.excess_sharpe(r2, f2))
    out["available"] = True
    return out


def is_available() -> bool:
    return _HAS_EP
