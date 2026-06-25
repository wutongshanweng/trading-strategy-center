"""Real WorldQuant Alpha101 formula — alpha072"""
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
class Alpha072_en(AlphaFactor):
    """alpha072: rank(decay_linear(correlation(((high+low)/2),adv40,8.9),10.2))/rank(decay_linear(correlation(ts_rank(vwap,3.7),ts_rank(volume,18.5),7),3))"""

    @property
    def name(self) -> str:
        return "alpha_en_072"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "rank(decay_linear(correlation(((high+low)/2),adv40,8.9),10.2))/rank(decay_linear(correlation(ts_rank(vwap,3.7),ts_rank(volume,18.5),7),3))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv40 = ts_mean(data["volume"], 40)
        mid = (data["high"] + data["low"]) / 2
        corr1 = correlation(mid, adv40, 9)
        decay1 = decay_linear(corr1, 10)
        rank1 = rank(decay1)
        ts_rank_vwap = ts_rank(data["vwap"], 4)
        ts_rank_vol = ts_rank(data["volume"], 19)
        corr2 = correlation(ts_rank_vwap, ts_rank_vol, 7)
        decay2 = decay_linear(corr2, 3)
        rank2 = rank(decay2)
        return rank1 / (rank2 + 1e-9)
