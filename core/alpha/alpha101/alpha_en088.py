"""Real WorldQuant Alpha101 formula — alpha088"""
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
class Alpha088_en(AlphaFactor):
    """alpha088: min(rank(decay_linear(((rank(open)+rank(low))-(rank(high)+rank(close))),8.1)),ts_rank(decay_linear(correlation(ts_rank(close,8.4),ts_rank(adv60,20.7),8),6.7),2.6))"""

    @property
    def name(self) -> str:
        return "alpha_en_088"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "min(rank(decay_linear(((rank(open)+rank(low))-(rank(high)+rank(close))),8.1)),ts_rank(decay_linear(correlation(ts_rank(close,8.4),ts_rank(adv60,20.7),8),6.7),2.6))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv60 = ts_mean(data["volume"], 60)
        inner = (rank(data["open"]) + rank(data["low"])) - (rank(data["high"]) + rank(data["close"]))
        decay1 = decay_linear(inner, 8)
        rank1 = rank(decay1)
        ts_rank_close = ts_rank(data["close"], 8)
        ts_rank_adv = ts_rank(adv60, 21)
        corr = correlation(ts_rank_close, ts_rank_adv, 8)
        decay2 = decay_linear(corr, 7)
        ts_rank2 = ts_rank(decay2, 3)
        return pd.concat([rank1, ts_rank2], axis=1).min(axis=1)
