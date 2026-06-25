"""Real WorldQuant Alpha101 formula — alpha073"""
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
class Alpha073_en(AlphaFactor):
    """alpha073: (max(rank(decay_linear(delta(vwap,4.7),2.9)),ts_rank(decay_linear(((delta(((open*0.15)+(low*(1-0.15))),2)/((open*0.15)+(low*(1-0.15))))*-1),3.3),16.7))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_073"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "(max(rank(decay_linear(delta(vwap,4.7),2.9)),ts_rank(decay_linear(((delta(((open*0.15)+(low*(1-0.15))),2)/((open*0.15)+(low*(1-0.15))))*-1),3.3),16.7))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        delta_vwap = delta(data["vwap"], 5)
        decay1 = decay_linear(delta_vwap, 3)
        rank1 = rank(decay1)
        weighted_open = (data["open"] * 0.15) + (data["low"] * 0.85)
        weighted_low = (data["open"] * 0.15) + (data["low"] * 0.85)
        delta_weighted = delta(weighted_open, 2)
        ratio = (delta_weighted / (weighted_low + 1e-9)) * -1
        decay2 = decay_linear(ratio, 3)
        ts_rank2 = ts_rank(decay2, 17)
        combined = pd.concat([pd.Series(rank1.values), pd.Series(ts_rank2.values)], axis=1).max(axis=1)
        return combined * -1
