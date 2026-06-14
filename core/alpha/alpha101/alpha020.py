"""Real WorldQuant Alpha101 formula — Alpha020: (((-1 * correlation(rank(open), rank(volume), 8)) + correlation(rank(high), rank(volume), 8)) / 2)"""
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
class Alpha020(AlphaFactor):
    """Alpha020: (((-1 * correlation(rank(open), rank(volume), 8)) + correlation(rank(high), rank(volume), 8)) / 2)"""

    @property
    def name(self) -> str:
        return "alpha020"

    @property
    def category(self) -> str:
        return "price_momentum"

    @property
    def description(self) -> str:
        return "Alpha020: (((-1 * correlation(rank(open), rank(volume), 8)) + correlation(rank(high), rank(volume), 8)) / 2)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        co = -1 * correlation(rank(data["open"]), rank(data["volume"]), 8)
        ch = correlation(rank(data["high"]), rank(data["volume"]), 8)
        return (co + ch) / 2
