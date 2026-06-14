"""Real WorldQuant Alpha101 formula — Alpha029: (rank(1 - rank(close)) + rank(rank(correlation(rank(close), rank(volume), 5))))"""
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
class Alpha029(AlphaFactor):
    """Alpha029: (rank(1 - rank(close)) + rank(rank(correlation(rank(close), rank(volume), 5))))"""

    @property
    def name(self) -> str:
        return "alpha029"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha029: (rank(1 - rank(close)) + rank(rank(correlation(rank(close), rank(volume), 5))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        r1 = rank(1 - rank(data["close"]))
        corr = correlation(rank(data["close"]), rank(data["volume"]), 5)
        r2 = rank(rank(corr))
        return r1 + r2
