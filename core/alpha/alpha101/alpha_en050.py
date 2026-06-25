"""Real WorldQuant Alpha101 formula — alpha050"""
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
class Alpha050_en(AlphaFactor):
    """alpha050: -1*ts_max(rank(correlation(rank(volume),rank(vwap),5)),5)"""

    @property
    def name(self) -> str:
        return "alpha_en_050"

    @property
    def category(self) -> str:
        return "correlation"

    @property
    def description(self) -> str:
        return "-1*ts_max(rank(correlation(rank(volume),rank(vwap),5)),5)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        rank_vol = rank(data["volume"])
        rank_vwap = rank(data["vwap"])
        corr = correlation(rank_vol, rank_vwap, 5)
        rank_corr = rank(corr)
        ts_max_val = ts_max(rank_corr, 5)
        return -1 * ts_max_val
