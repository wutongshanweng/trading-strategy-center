"""Real WorldQuant Alpha101 formula — alpha027"""
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
class Alpha027_en(AlphaFactor):
    """alpha027: ((0.5<rank((sum(correlation(rank(volume),rank(vwap),6),2)/2.0)))?(-1*1):1)"""

    @property
    def name(self) -> str:
        return "alpha_en_027"

    @property
    def category(self) -> str:
        return "correlation"

    @property
    def description(self) -> str:
        return "((0.5<rank((sum(correlation(rank(volume),rank(vwap),6),2)/2.0)))?(-1*1):1)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        rank_vol = rank(data["volume"])
        rank_vwap = rank(data["vwap"])
        corr = correlation(rank_vol, rank_vwap, 6)
        sum_corr = ts_sum(corr, 2)
        avg_corr = sum_corr / 2.0
        rank_avg = rank(avg_corr)
        cond = rank_avg > 0.5
        return pd.Series(np.where(cond, -1.0, 1.0), index=data.index)
