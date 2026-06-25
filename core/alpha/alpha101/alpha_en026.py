"""Real WorldQuant Alpha101 formula — alpha026"""
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
class Alpha026_en(AlphaFactor):
    """alpha026: -1*ts_max(correlation(ts_rank(volume,5),ts_rank(high,5),5),3)"""

    @property
    def name(self) -> str:
        return "alpha_en_026"

    @property
    def category(self) -> str:
        return "correlation"

    @property
    def description(self) -> str:
        return "-1*ts_max(correlation(ts_rank(volume,5),ts_rank(high,5),5),3)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        ts_rank_vol = ts_rank(data["volume"], 5)
        ts_rank_high = ts_rank(data["high"], 5)
        corr = correlation(ts_rank_vol, ts_rank_high, 5)
        ts_max_corr = ts_max(corr, 3)
        return -1 * ts_max_corr
