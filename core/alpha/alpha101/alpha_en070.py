"""Real WorldQuant Alpha101 formula — alpha070"""
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
class Alpha070_en(AlphaFactor):
    """alpha070: (rank(delta(vwap,1.29))^ts_rank(correlation(close,adv50,17.8),17.9))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_070"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "(rank(delta(vwap,1.29))^ts_rank(correlation(close,adv50,17.8),17.9))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv50 = ts_mean(data["volume"], 50)
        delta_vwap = delta(data["vwap"], 1)
        rank1 = rank(delta_vwap)
        corr = correlation(data["close"], adv50, 18)
        ts_rank2 = ts_rank(corr, 18)
        return (rank1 ** ts_rank2) * -1
