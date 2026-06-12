import numpy as np
from typing import Dict, List


class CapitalAllocation:
    def __init__(self, total_capital: float):
        self.total_capital = total_capital
        self.buckets = {
            "trend": 0.25,
            "reversal": 0.15,
            "breakout": 0.20,
            "momentum": 0.15,
            "ml": 0.15,
            "reserve": 0.10,
        }

    def allocate(self, strategy_type: str, confidence: float) -> float:
        base = self.buckets.get(strategy_type, 0.05)
        return self.total_capital * base * confidence

    def risk_parity(self, volatilities: Dict[str, float]) -> Dict[str, float]:
        vols = np.array(list(volatilities.values()))
        inv_vol = 1.0 / np.maximum(vols, 1e-6)
        weights = inv_vol / inv_vol.sum()
        return dict(zip(volatilities.keys(), weights))
