"""Real WorldQuant Alpha101 formula — alpha076"""
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
class Alpha076_en(AlphaFactor):
    """alpha076: (max(rank(decay_linear(delta(vwap,1.2),11.8)),ts_rank(decay_linear(ts_rank(correlation(low,adv80,8.1),19.6),17.2),19.4))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_076"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "(max(rank(decay_linear(delta(vwap,1.2),11.8)),ts_rank(decay_linear(ts_rank(correlation(low,adv80,8.1),19.6),17.2),19.4))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv80 = ts_mean(data["volume"], 80)
        delta_vwap = delta(data["vwap"], 1)
        decay1 = decay_linear(delta_vwap, 12)
        rank1 = rank(decay1)
        corr = correlation(data["low"], adv80, 8)
        ts_rank_corr = ts_rank(corr, 20)
        decay2 = decay_linear(ts_rank_corr, 17)
        ts_rank2 = ts_rank(decay2, 19)
        combined = pd.concat([pd.Series(rank1.values), pd.Series(ts_rank2.values)], axis=1).max(axis=1)
        return combined * -1
