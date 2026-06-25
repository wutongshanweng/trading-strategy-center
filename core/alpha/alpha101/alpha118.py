"""Real WorldQuant Alpha101 formula — Momentum alpha118: SUM(high - open, 20) / SUM(open - low, 20) * 100"""
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
class Alpha118(AlphaFactor):
    """Momentum alpha118: SUM(high - open, 20) / SUM(open - low, 20) * 100"""

    @property
    def name(self) -> str:
        return "alpha118"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha118: SUM(high - open, 20) / SUM(open - low, 20) * 100"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        up_range = ts_sum(data["high"] - data["open"], 20)
        down_range = ts_sum(data["open"] - data["low"], 20)
        return (up_range / (down_range + 1e-8)) * 100
