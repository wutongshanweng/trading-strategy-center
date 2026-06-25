"""Real WorldQuant Alpha101 formula — Momentum alpha105: -1 * correlation(rank(open), rank(volume), 10)"""
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
class Alpha105(AlphaFactor):
    """Momentum alpha105: -1 * correlation(rank(open), rank(volume), 10)"""

    @property
    def name(self) -> str:
        return "alpha105"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha105: -1 * correlation(rank(open), rank(volume), 10)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        rank_open = rank(data["open"])
        rank_vol = rank(data["volume"])
        corr = correlation(rank_open, rank_vol, 10)
        return -1 * corr
