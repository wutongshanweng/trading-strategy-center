"""Real WorldQuant Alpha101 formula — alpha078"""
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
class Alpha078_en(AlphaFactor):
    """alpha078: rank(correlation(sum(((low*0.35)+(vwap*(1-0.35))),19.7),sum(adv40,19.7),6.8))^rank(correlation(rank(vwap),rank(volume),5.8))"""

    @property
    def name(self) -> str:
        return "alpha_en_078"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "rank(correlation(sum(((low*0.35)+(vwap*(1-0.35))),19.7),sum(adv40,19.7),6.8))^rank(correlation(rank(vwap),rank(volume),5.8))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv40 = ts_mean(data["volume"], 40)
        weighted = (data["low"] * 0.35) + (data["vwap"] * 0.65)
        sum_weighted = ts_sum(weighted, 20)
        sum_adv = ts_sum(adv40, 20)
        corr1 = correlation(sum_weighted, sum_adv, 7)
        rank1 = rank(corr1)
        rank_vwap = rank(data["vwap"])
        rank_vol = rank(data["volume"])
        corr2 = correlation(rank_vwap, rank_vol, 6)
        rank2 = rank(corr2)
        return rank1 ** rank2
