"""Real WorldQuant Alpha101 formula — alpha097"""
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
class Alpha097_en(AlphaFactor):
    """alpha097: (rank(decay_linear(delta(close,3.4),20.5))-ts_rank(decay_linear(ts_rank(correlation(ts_rank(low,7.9),ts_rank(adv60,17.3),5),18.6),15.7),6.7))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_097"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "(rank(decay_linear(delta(close,3.4),20.5))-ts_rank(decay_linear(ts_rank(correlation(ts_rank(low,7.9),ts_rank(adv60,17.3),5),18.6),15.7),6.7))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv60 = ts_mean(data["volume"], 60)
        delta_close = delta(data["close"], 3)
        decay1 = decay_linear(delta_close, 21)
        rank1 = rank(decay1)
        ts_rank_low = ts_rank(data["low"], 8)
        ts_rank_adv = ts_rank(adv60, 17)
        corr = correlation(ts_rank_low, ts_rank_adv, 5)
        ts_rank_corr = ts_rank(corr, 19)
        decay2 = decay_linear(ts_rank_corr, 16)
        ts_rank2 = ts_rank(decay2, 7)
        return (rank1 - ts_rank2) * -1
