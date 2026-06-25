"""Real WorldQuant Alpha101 formula — Momentum alpha189: mean(ABS(close - mean(close, 6)), 6)"""
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
class Alpha189(AlphaFactor):
    """Momentum alpha189: mean(ABS(close - mean(close, 6)), 6)"""

    @property
    def name(self) -> str:
        return "alpha189"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha189: mean(ABS(close - mean(close, 6)), 6)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        mean_close = ts_mean(data["close"], 6)
        abs_diff = np.abs(data["close"] - mean_close)
        return ts_mean(abs_diff, 6)
