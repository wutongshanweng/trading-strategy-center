"""Real WorldQuant Alpha101 formula — Momentum alpha133: ((20 - highday(high, 20)) / 20) * 100 - ((20 - lowday(low, 20)) / 20) * 100"""
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
class Alpha133(AlphaFactor):
    """Momentum alpha133: ((20 - highday(high, 20)) / 20) * 100 - ((20 - lowday(low, 20)) / 20) * 100"""

    @property
    def name(self) -> str:
        return "alpha133"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha133: ((20 - highday(high, 20)) / 20) * 100 - ((20 - lowday(low, 20)) / 20) * 100"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # highday: number of days since the highest high
        def days_since_high(s):
            if len(s) == 0:
                return 20
            argmax_idx = np.argmax(s)
            return len(s) - 1 - argmax_idx

        def days_since_low(s):
            if len(s) == 0:
                return 20
            argmin_idx = np.argmin(s)
            return len(s) - 1 - argmin_idx

        highday = data["high"].rolling(20, min_periods=20).apply(days_since_high, raw=True)
        lowday = data["low"].rolling(20, min_periods=20).apply(days_since_low, raw=True)

        return ((20 - highday) / 20) * 100 - ((20 - lowday) / 20) * 100
