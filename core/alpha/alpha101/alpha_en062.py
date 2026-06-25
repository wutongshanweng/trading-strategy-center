"""Real WorldQuant Alpha101 formula — alpha062"""
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
class Alpha062_en(AlphaFactor):
    """alpha062: (rank(correlation(vwap,sum(adv20,22.4),9.9))<rank(((rank(open)+rank(open))<(rank(((high+low)/2))+rank(high)))))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_062"

    @property
    def category(self) -> str:
        return "comparison"

    @property
    def description(self) -> str:
        return "(rank(correlation(vwap,sum(adv20,22.4),9.9))<rank(((rank(open)+rank(open))<(rank(((high+low)/2))+rank(high)))))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv20 = ts_mean(data["volume"], 20)
        sum_adv = ts_sum(adv20, 22)
        corr = correlation(data["vwap"], sum_adv, 10)
        rank1 = rank(corr)
        rank_open = rank(data["open"])
        rank_open_sum = rank_open + rank_open
        mid = (data["high"] + data["low"]) / 2
        rank_mid = rank(mid)
        rank_high = rank(data["high"])
        rank2 = rank_mid + rank_high
        cond = rank_open_sum < rank2
        return pd.Series(np.where(cond, -1.0, 0.0), index=data.index)
