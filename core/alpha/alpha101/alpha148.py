"""Real WorldQuant Alpha101 formula — Momentum alpha148: (rank(correlation((open), sum(mean(volume, 60), 9), 6)) < rank((open - tsmin(open, 14)))) * -1"""
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
class Alpha148(AlphaFactor):
    """Momentum alpha148: (rank(correlation((open), sum(mean(volume, 60), 9), 6)) < rank((open - tsmin(open, 14)))) * -1"""

    @property
    def name(self) -> str:
        return "alpha148"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha148: (rank(correlation((open), sum(mean(volume, 60), 9), 6)) < rank((open - tsmin(open, 14)))) * -1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        sum_vol = ts_sum(ts_mean(data["volume"], 60), 9)
        corr = correlation(data["open"], sum_vol, 6)
        rank_corr = rank(corr)

        min_open = ts_min(data["open"], 14)
        open_diff = data["open"] - min_open
        rank_open = rank(open_diff)

        return (rank_corr < rank_open).astype(float) * -1
