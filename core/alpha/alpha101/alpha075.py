"""Real WorldQuant Alpha101 formula — Alpha075: (rank(correlation(vwap, volume, 4)) < rank(correlation(rank(low), rank(adv50), 12)))"""
import numpy as np
import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .operators import (
    rank, ts_rank, ts_argmax, ts_argmin, ts_sum, ts_product,
    ts_min, ts_max, ts_mean, ts_std, ts_cov, correlation, covariance,
    scale, delay, delta, signedpower, decay_linear, signed_sqrt, bool_to_float,
)


@FactorRegistry.register
class Alpha075(AlphaFactor):
    """Alpha075: (rank(correlation(vwap, volume, 4)) < rank(correlation(rank(low), rank(adv50), 12)))"""

    @property
    def name(self) -> str:
        return "alpha075"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha075: (rank(correlation(vwap, volume, 4)) < rank(correlation(rank(low), rank(adv50), 12)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        adv50 = data["volume"].rolling(50, min_periods=10).mean()
        left = rank(correlation(vwap, data["volume"], 4))
        right = rank(correlation(rank(data["low"]), rank(adv50), 12))
        return bool_to_float(left < right, left, right)
