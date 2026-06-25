"""Real WorldQuant Alpha101 formula — alpha082"""
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
class Alpha082_en(AlphaFactor):
    """alpha082: min(rank(decay_linear(delta(open,1.5),14.9)),ts_rank(decay_linear(correlation(volume,((open*0.63)+(open*(1-0.63))),17.5),6.9),13.4))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_082"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "min(rank(decay_linear(delta(open,1.5),14.9)),ts_rank(decay_linear(correlation(volume,((open*0.63)+(open*(1-0.63))),17.5),6.9),13.4))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        delta_open = delta(data["open"], 2)
        decay1 = decay_linear(delta_open, 15)
        rank1 = rank(decay1)
        weighted_open = (data["open"] * 0.63) + (data["open"] * 0.37)
        corr = correlation(data["volume"], weighted_open, 18)
        decay2 = decay_linear(corr, 7)
        ts_rank2 = ts_rank(decay2, 13)
        combined = pd.concat([pd.Series(rank1.values), pd.Series(ts_rank2.values)], axis=1).min(axis=1)
        return combined * -1
