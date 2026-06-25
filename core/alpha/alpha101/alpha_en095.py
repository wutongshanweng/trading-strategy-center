"""Real WorldQuant Alpha101 formula — alpha095"""
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
class Alpha095_en(AlphaFactor):
    """alpha095: rank((open-ts_min(open,12.4)))<ts_rank((rank(correlation(sum(((high+low)/2),19.1),sum(adv40,19.1),12.9))**5),11.8)"""

    @property
    def name(self) -> str:
        return "alpha_en_095"

    @property
    def category(self) -> str:
        return "comparison"

    @property
    def description(self) -> str:
        return "rank((open-ts_min(open,12.4)))<ts_rank((rank(correlation(sum(((high+low)/2),19.1),sum(adv40,19.1),12.9))**5),11.8)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv40 = ts_mean(data["volume"], 40)
        open_min = data["open"] - ts_min(data["open"], 12)
        rank1 = rank(open_min)
        mid = (data["high"] + data["low"]) / 2
        sum_mid = ts_sum(mid, 19)
        sum_adv = ts_sum(adv40, 19)
        corr = correlation(sum_mid, sum_adv, 13)
        inner = rank(corr) ** 5
        ts_rank2 = ts_rank(inner, 12)
        return (rank1 < ts_rank2).astype(float)
