"""Real WorldQuant Alpha101 formula — alpha091"""
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
class Alpha091_en(AlphaFactor):
    """alpha091: (ts_rank(decay_linear(decay_linear(correlation(close,volume,9.7),16.4),3.8),4.9)-rank(decay_linear(correlation(vwap,adv30,4),2.7)))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_091"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "(ts_rank(decay_linear(decay_linear(correlation(close,volume,9.7),16.4),3.8),4.9)-rank(decay_linear(correlation(vwap,adv30,4),2.7)))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv30 = ts_mean(data["volume"], 30)
        corr1 = correlation(data["close"], data["volume"], 10)
        decay1 = decay_linear(corr1, 16)
        decay2 = decay_linear(decay1, 4)
        ts_rank1 = ts_rank(decay2, 5)
        corr2 = correlation(data["vwap"], adv30, 4)
        decay3 = decay_linear(corr2, 3)
        rank2 = rank(decay3)
        return (ts_rank1 - rank2) * -1
