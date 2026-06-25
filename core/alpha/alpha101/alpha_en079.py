"""Real WorldQuant Alpha101 formula — alpha079"""
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
class Alpha079_en(AlphaFactor):
    """alpha079: rank(delta(close,1.2))<rank(correlation(ts_rank(vwap,3.6),ts_rank(adv150,9.2),14.7))"""

    @property
    def name(self) -> str:
        return "alpha_en_079"

    @property
    def category(self) -> str:
        return "comparison"

    @property
    def description(self) -> str:
        return "rank(delta(close,1.2))<rank(correlation(ts_rank(vwap,3.6),ts_rank(adv150,9.2),14.7))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv150 = ts_mean(data["volume"], 150)
        delta_close = delta(data["close"], 1)
        rank1 = rank(delta_close)
        ts_rank_vwap = ts_rank(data["vwap"], 4)
        ts_rank_adv = ts_rank(adv150, 9)
        corr = correlation(ts_rank_vwap, ts_rank_adv, 15)
        rank2 = rank(corr)
        return (rank1 < rank2).astype(float)
