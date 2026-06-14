"""Volatility-targeting position sizing."""

from __future__ import annotations

import numpy as np


class VolatilityTargeting:
    """Adjust position size to target a given annualised volatility."""

    def __init__(self, target_vol: float = 0.15, lookback: int = 20):
        self.target_vol = target_vol
        self.lookback = lookback

    def calculate_position_size(self, returns: np.ndarray) -> float:
        """Return a multiplier (0.1 – 2.0) based on recent vol."""
        recent = returns[-self.lookback:] if len(returns) >= self.lookback else returns
        vol = float(np.std(recent)) * np.sqrt(252)
        if vol == 0:
            return 1.0
        size = self.target_vol / vol
        return max(0.1, min(size, 2.0))

    def adjust_position(self, current: float, returns: np.ndarray) -> float:
        """Smoothly adjust toward the target."""
        target = self.calculate_position_size(returns)
        return current + (target - current) * 0.1
