"""Real WorldQuant Alpha101 formula — alpha064"""
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
class Alpha064_en(AlphaFactor):
    """alpha064: (rank(correlation(sum(((open*0.18)+(low*(1-0.18))),12.7),sum(adv120,12.7),16.6))<rank(delta(((((high+low)/2)*0.18)+(vwap*(1-0.18))),3.7)))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_064"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "(rank(correlation(sum(((open*0.18)+(low*(1-0.18))),12.7),sum(adv120,12.7),16.6))<rank(delta(((((high+low)/2)*0.18)+(vwap*(1-0.18))),3.7)))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv120 = ts_mean(data["volume"], 120)
        weighted_open = (data["open"] * 0.18) + (data["low"] * 0.82)
        sum_weighted = ts_sum(weighted_open, 13)
        sum_adv = ts_sum(adv120, 13)
        corr = correlation(sum_weighted, sum_adv, 17)
        rank1 = rank(corr)
        mid = (data["high"] + data["low"]) / 2
        weighted_mid = (mid * 0.18) + (data["vwap"] * 0.82)
        delta_weighted = delta(weighted_mid, 4)
        rank2 = rank(delta_weighted)
        cond = rank1 < rank2
        return pd.Series(np.where(cond, -1.0, 0.0), index=data.index)
