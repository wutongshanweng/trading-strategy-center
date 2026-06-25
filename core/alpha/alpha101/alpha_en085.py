"""Real WorldQuant Alpha101 formula — alpha085"""
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
class Alpha085_en(AlphaFactor):
    """alpha085: rank(correlation(((high*0.88)+(close*(1-0.88))),adv30,9.6))^rank(correlation(ts_rank(((high+low)/2),3.7),ts_rank(volume,10.2),7.1))"""

    @property
    def name(self) -> str:
        return "alpha_en_085"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "rank(correlation(((high*0.88)+(close*(1-0.88))),adv30,9.6))^rank(correlation(ts_rank(((high+low)/2),3.7),ts_rank(volume,10.2),7.1))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv30 = ts_mean(data["volume"], 30)
        weighted = (data["high"] * 0.88) + (data["close"] * 0.12)
        corr1 = correlation(weighted, adv30, 10)
        rank1 = rank(corr1)
        mid = (data["high"] + data["low"]) / 2
        ts_rank_mid = ts_rank(mid, 4)
        ts_rank_vol = ts_rank(data["volume"], 10)
        corr2 = correlation(ts_rank_mid, ts_rank_vol, 7)
        rank2 = rank(corr2)
        return rank1 ** rank2
