"""Real WorldQuant Alpha101 formula — Alpha068: (-1 * (ts_rank(correlation(rank(high), rank(adv15), 9), 14) < rank(delta((close * 0.518371) + (low * (1 - 0.518371)), 1))))"""
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
class Alpha068(AlphaFactor):
    """Alpha068: (-1 * (ts_rank(correlation(rank(high), rank(adv15), 9), 14) < rank(delta((close * 0.518371) + (low * (1 - 0.518371)), 1))))"""

    @property
    def name(self) -> str:
        return "alpha068"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha068: (-1 * (ts_rank(correlation(rank(high), rank(adv15), 9), 14) < rank(delta((close * 0.518371) + (low * (1 - 0.518371)), 1))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv15 = data["volume"].rolling(15).mean()
        blended = data["close"] * 0.518371 + data["low"] * 0.481629
        left = ts_rank(correlation(rank(data["high"]), rank(adv15), 9), 14)
        right = rank(delta(blended, 1))
        return bool_to_float(left < right, left, right, sign=-1.0)
