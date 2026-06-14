"""Conditional Value at Risk (CVaR / Expected Shortfall)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .var_calculator import VaRCalculator


class CVaRCalculator:
    """Calculate CVaR (Expected Shortfall) at a given confidence level."""

    def __init__(self, confidence: float = 0.95):
        self.confidence = confidence

    def calculate(self, returns: pd.Series) -> float:
        """CVaR = average loss beyond VaR."""
        sorted_r = np.sort(returns.dropna().values)
        cutoff = int((1 - self.confidence) * len(sorted_r))
        if cutoff < 1:
            cutoff = 1
        tail = sorted_r[:cutoff]
        return float(-tail.mean()) if len(tail) > 0 else 0.0

    def conditional_expected_shortfall(self, returns: pd.Series) -> float:
        """Alias for calculate — expected shortfall in the tail."""
        return self.calculate(returns)
