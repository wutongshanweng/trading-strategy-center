"""Real WorldQuant Alpha101 formula — alpha015"""
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
class Alpha015_en(AlphaFactor):
    """alpha015: -1*sum(rank(correlation(rank(high),rank(volume),3)),3)"""

    @property
    def name(self) -> str:
        return "alpha_en_015"

    @property
    def category(self) -> str:
        return "correlation"

    @property
    def description(self) -> str:
        return "-1*sum(rank(correlation(rank(high),rank(volume),3)),3)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        rank_high = rank(data["high"])
        rank_vol = rank(data["volume"])
        corr = correlation(rank_high, rank_vol, 3)
        rank_corr = rank(corr)
        result = ts_sum(rank_corr, 3)
        return -1 * result
