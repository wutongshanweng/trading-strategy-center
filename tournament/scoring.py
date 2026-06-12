from typing import Dict, List
import numpy as np


def calculate_composite_score(stats: Dict[str, float]) -> float:
    weights = {"sharpe": 0.40, "win_rate": 0.25, "profit_factor": 0.15, "max_drawdown": 0.10, "trade_count": 0.10}
    score = 0.0
    if "sharpe" in stats:
        score += weights["sharpe"] * min(max(stats["sharpe"] * 10, 0), 100)
    if "win_rate" in stats:
        score += weights["win_rate"] * stats["win_rate"] * 100
    if "profit_factor" in stats:
        score += weights["profit_factor"] * min(stats["profit_factor"] * 10, 100)
    if "max_drawdown" in stats:
        score -= weights["max_drawdown"] * min(abs(stats["max_drawdown"]) * 100, 100)
    if "trade_count" in stats:
        score += weights["trade_count"] * min(stats["trade_count"], 100)
    return max(0, min(score, 100))


def calculate_sharpe(pnls: List[float]) -> float:
    arr = np.array(pnls)
    if len(arr) < 2 or arr.std() == 0:
        return 0.0
    return float(arr.mean() / arr.std() * np.sqrt(252))


def calculate_max_drawdown(equity_curve: List[float]) -> float:
    arr = np.array(equity_curve)
    if len(arr) < 2:
        return 0.0
    peak = np.maximum.accumulate(arr)
    return float(((arr - peak) / peak).min())


def calculate_profit_factor(pnls: List[float]) -> float:
    gross_profit = sum(p for p in pnls if p > 0)
    gross_loss = abs(sum(p for p in pnls if p < 0))
    return gross_profit / gross_loss if gross_loss > 0 else float("inf")


def calculate_win_rate(pnls: List[float]) -> float:
    if not pnls:
        return 0.0
    return sum(1 for p in pnls if p > 0) / len(pnls)
