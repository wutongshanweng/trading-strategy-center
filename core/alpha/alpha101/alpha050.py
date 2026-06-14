"""Real WorldQuant Alpha101 formula — Alpha050: (-1 * ts_max(rank(correlation(rank(volume), rank(vwap), 5)), 5))"""
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
class Alpha050(AlphaFactor):
    """Alpha050: (-1 * ts_max(rank(correlation(rank(volume), rank(vwap), 5)), 5))"""

    @property
    def name(self) -> str:
        return "alpha050"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha050: (-1 * ts_max(rank(correlation(rank(volume), rank(vwap), 5)), 5))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        return -1 * ts_max(rank(correlation(rank(data["volume"]), rank(vwap), 5)), 5)
