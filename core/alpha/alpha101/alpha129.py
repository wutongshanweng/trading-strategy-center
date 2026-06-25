"""Real WorldQuant Alpha101 formula — Momentum alpha129: SUM(ABS(close - delay(close, 1)), 12)"""
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
class Alpha129(AlphaFactor):
    """Momentum alpha129: SUM(ABS(close - delay(close, 1)), 12) — sum of absolute price changes"""

    @property
    def name(self) -> str:
        return "alpha129"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha129: SUM(ABS(close - delay(close, 1)), 12) — sum of absolute price changes"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        abs_change = np.abs(data["close"] - delay(data["close"], 1))
        return ts_sum(abs_change, 12)
