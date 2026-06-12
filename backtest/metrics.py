import numpy as np
from typing import List


def sharpe_ratio(returns: List[float], risk_free: float = 0.03) -> float:
    arr = np.array(returns)
    if len(arr) < 2 or arr.std() == 0:
        return 0.0
    excess = arr.mean() * 252 - risk_free
    return float(excess / (arr.std() * np.sqrt(252)))


def max_drawdown(equity_curve: List[float]) -> float:
    arr = np.array(equity_curve)
    if len(arr) < 2:
        return 0.0
    peak = np.maximum.accumulate(arr)
    dd = (arr - peak) / peak
    return float(dd.min())


def calmar_ratio(returns: List[float], equity_curve: List[float]) -> float:
    ann_return = np.mean(returns) * 252 if returns else 0
    mdd = max_drawdown(equity_curve)
    return float(ann_return / abs(mdd)) if mdd != 0 else 0.0


def win_rate(pnls: List[float]) -> float:
    if not pnls:
        return 0.0
    return sum(1 for p in pnls if p > 0) / len(pnls)


def profit_factor(pnls: List[float]) -> float:
    gross_profit = sum(p for p in pnls if p > 0)
    gross_loss = abs(sum(p for p in pnls if p < 0))
    return float(gross_profit / gross_loss) if gross_loss > 0 else float("inf")


def sortino_ratio(returns: List[float], risk_free: float = 0.03) -> float:
    arr = np.array(returns)
    if len(arr) < 2:
        return 0.0
    excess = arr.mean() * 252 - risk_free
    downside = arr[arr < 0]
    if len(downside) < 2 or downside.std() == 0:
        return 0.0
    return float(excess / (downside.std() * np.sqrt(252)))
