"""Real WorldQuant Alpha101 formula — Momentum alpha177: ((20 - highday(high, 20)) / 20) * 100"""
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
class Alpha177(AlphaFactor):
    """Momentum alpha177: ((20 - highday(high, 20)) / 20) * 100"""

    @property
    def name(self) -> str:
        return "alpha177"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha177: ((20 - highday(high, 20)) / 20) * 100"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        def days_since_high(s):
            if len(s) == 0:
                return 20
            argmax_idx = np.argmax(s)
            return len(s) - 1 - argmax_idx

        highday = data["high"].rolling(20, min_periods=20).apply(days_since_high, raw=True)
        return ((20 - highday) / 20) * 100
