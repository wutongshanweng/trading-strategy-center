"""Real WorldQuant Alpha101 formula — alpha074"""
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
class Alpha074_en(AlphaFactor):
    """alpha074: (rank(correlation(close,sum(adv30,37.5),15.1))<rank(correlation(rank(((high*0.026)+(vwap*(1-0.026)))),rank(volume),11.5)))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_074"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "(rank(correlation(close,sum(adv30,37.5),15.1))<rank(correlation(rank(((high*0.026)+(vwap*(1-0.026)))),rank(volume),11.5)))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv30 = ts_mean(data["volume"], 30)
        sum_adv = ts_sum(adv30, 38)
        corr1 = correlation(data["close"], sum_adv, 15)
        rank1 = rank(corr1)
        weighted = (data["high"] * 0.026) + (data["vwap"] * 0.974)
        rank_weighted = rank(weighted)
        rank_vol = rank(data["volume"])
        corr2 = correlation(rank_weighted, rank_vol, 12)
        rank2 = rank(corr2)
        cond = rank1 < rank2
        return pd.Series(np.where(cond, -1.0, 0.0), index=data.index)
