"""Real WorldQuant Alpha101 formula — Momentum alpha123: (rank(correlation(sum((high + low) / 2, 20), sum(mean(volume, 60), 20), 9)) < rank(correlation(low, volume, 6))) * -1"""
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
class Alpha123(AlphaFactor):
    """Momentum alpha123: (rank(correlation(sum((high + low) / 2, 20), sum(mean(volume, 60), 20), 9)) < rank(correlation(low, volume, 6))) * -1"""

    @property
    def name(self) -> str:
        return "alpha123"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha123: (rank(correlation(sum((high + low) / 2, 20), sum(mean(volume, 60), 20), 9)) < rank(correlation(low, volume, 6))) * -1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        hl = (data["high"] + data["low"]) / 2
        sum_hl = ts_sum(hl, 20)
        sum_vol = ts_sum(ts_mean(data["volume"], 60), 20)
        corr1 = correlation(sum_hl, sum_vol, 9)
        rank_corr1 = rank(corr1)

        corr2 = correlation(data["low"], data["volume"], 6)
        rank_corr2 = rank(corr2)

        return (rank_corr1 < rank_corr2).astype(float) * -1
