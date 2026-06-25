"""Real WorldQuant Alpha101 formula — alpha065"""
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
class Alpha065_en(AlphaFactor):
    """alpha065: (rank(correlation(((open*0.008)+(vwap*(1-0.008))),sum(adv60,8.7),6.4))<rank((open-ts_min(open,13.6))))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_065"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "(rank(correlation(((open*0.008)+(vwap*(1-0.008))),sum(adv60,8.7),6.4))<rank((open-ts_min(open,13.6))))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv60 = ts_mean(data["volume"], 60)
        sum_adv = ts_sum(adv60, 9)
        weighted = (data["open"] * 0.008) + (data["vwap"] * 0.992)
        corr = correlation(weighted, sum_adv, 6)
        rank1 = rank(corr)
        open_min = data["open"] - ts_min(data["open"], 14)
        rank2 = rank(open_min)
        cond = rank1 < rank2
        return pd.Series(np.where(cond, -1.0, 0.0), index=data.index)
