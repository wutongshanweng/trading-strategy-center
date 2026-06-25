"""Real WorldQuant Alpha101 formula — alpha099"""
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
class Alpha099_en(AlphaFactor):
    """alpha099: ((rank(correlation(sum(((high+low)/2),19.9),sum(adv60,19.9),8.8))<rank(correlation(low,volume,6.3)))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_099"

    @property
    def category(self) -> str:
        return "comparison"

    @property
    def description(self) -> str:
        return "((rank(correlation(sum(((high+low)/2),19.9),sum(adv60,19.9),8.8))<rank(correlation(low,volume,6.3)))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv60 = ts_mean(data["volume"], 60)
        mid = (data["high"] + data["low"]) / 2
        sum_mid = ts_sum(mid, 20)
        sum_adv = ts_sum(adv60, 20)
        corr1 = correlation(sum_mid, sum_adv, 9)
        rank1 = rank(corr1)
        corr2 = correlation(data["low"], data["volume"], 6)
        rank2 = rank(corr2)
        cond = rank1 < rank2
        return pd.Series(np.where(cond, -1.0, 0.0), index=data.index)
