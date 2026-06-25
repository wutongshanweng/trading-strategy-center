"""Real WorldQuant Alpha101 formula — alpha067"""
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
class Alpha067_en(AlphaFactor):
    """alpha067: (rank((high-ts_min(high,2.1)))^rank(correlation(vwap,mean(volume,6),6)))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_067"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "(rank((high-ts_min(high,2.1)))^rank(correlation(vwap,mean(volume,6),6)))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        high_min = data["high"] - ts_min(data["high"], 2)
        rank1 = rank(high_min)
        mean_vol = ts_mean(data["volume"], 6)
        corr = correlation(data["vwap"], mean_vol, 6)
        rank2 = rank(corr)
        return (rank1 ** rank2) * -1
