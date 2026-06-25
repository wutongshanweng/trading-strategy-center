"""Real WorldQuant Alpha101 formula — Reversal alpha103: (20-LOWDAY(LOW,20))/20*100"""
import numpy as np
import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .operators import (
    rank, ts_rank, ts_argmax, ts_argmin, ts_sum, ts_product,
    ts_min, ts_max, ts_mean, ts_std, ts_cov, correlation, covariance,
    scale, delay, delta, signedpower, decay_linear, signed_sqrt,
)


@FactorRegistry.register
class Alpha103(AlphaFactor):
    """Reversal alpha103: (20-LOWDAY(LOW,20))/20*100 — (20 minus days since low) / 20 * 100"""

    @property
    def name(self) -> str:
        return "alpha103"

    @property
    def category(self) -> str:
        return "reversal"

    @property
    def description(self) -> str:
        return "Reversal alpha103: (20-LOWDAY(LOW,20))/20*100 — (20 minus days since low) / 20 * 100"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        low = data["low"]
        # LOWDAY: number of days since the lowest low in the window
        # Find days since low using rolling argmin
        def days_since_low(s):
            if len(s) == 0:
                return 20
            argmin_idx = np.argmin(s)
            return len(s) - 1 - argmin_idx
        lowday = low.rolling(20, min_periods=20).apply(days_since_low, raw=True)
        return (20 - lowday) / 20 * 100
