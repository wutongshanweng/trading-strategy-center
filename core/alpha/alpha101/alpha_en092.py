"""Real WorldQuant Alpha101 formula — alpha092"""
import numpy as np
import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .operators import (
    rank, ts_rank, ts_argmax, ts_argmin, ts_sum, ts_product,
    ts_max, ts_mean, ts_std, ts_cov, correlation, covariance,
    scale, delay, delta, signedpower, decay_linear, signed_sqrt,
)


@FactorRegistry.register
class Alpha092_en(AlphaFactor):
    """alpha092: min(ts_rank(decay_linear(((((high+low)/2)+close)<(low+open),14.7),18.9),ts_rank(decay_linear(correlation(rank(low),rank(adv30),7.6),6.9),6.8))"""

    @property
    def name(self) -> str:
        return "alpha_en_092"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "min(ts_rank(decay_linear(((((high+low)/2)+close)<(low+open),14.7),18.9),ts_rank(decay_linear(correlation(rank(low),rank(adv30),7.6),6.9),6.8))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv30 = ts_mean(data["volume"], 30)
        mid = (data["high"] + data["low"]) / 2
        condition = ((mid + data["close"]) < (data["low"] + data["open"])).astype(float)
        decay1 = decay_linear(condition, 15)
        ts_rank1 = ts_rank(decay1, 19)
        rank_low = rank(data["low"])
        rank_adv = rank(adv30)
        corr = correlation(rank_low, rank_adv, 8)
        decay2 = decay_linear(corr, 7)
        ts_rank2 = ts_rank(decay2, 7)
        return pd.concat([ts_rank1, ts_rank2], axis=1).min(axis=1)
