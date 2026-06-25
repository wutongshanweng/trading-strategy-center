"""Real WorldQuant Alpha101 formula — Momentum alpha141: rank(correlation(rank(high), rank(mean(volume, 15)), 9)) * -1"""
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
class Alpha141(AlphaFactor):
    """Momentum alpha141: rank(correlation(rank(high), rank(mean(volume, 15)), 9)) * -1"""

    @property
    def name(self) -> str:
        return "alpha141"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha141: rank(correlation(rank(high), rank(mean(volume, 15)), 9)) * -1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        rank_high = rank(data["high"])
        rank_mean_vol = rank(ts_mean(data["volume"], 15))
        corr = correlation(rank_high, rank_mean_vol, 9)
        return rank(corr) * -1
