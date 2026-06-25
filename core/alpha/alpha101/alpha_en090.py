"""Real WorldQuant Alpha101 formula — alpha090"""
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
class Alpha090_en(AlphaFactor):
    """alpha090: ((rank((close-ts_max(close,4.7)))^ts_rank(correlation(low,adv40,5.4),3.2))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_090"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "((rank((close-ts_max(close,4.7)))^ts_rank(correlation(low,adv40,5.4),3.2))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv40 = ts_mean(data["volume"], 40)
        close_max = data["close"] - ts_max(data["close"], 5)
        rank1 = rank(close_max)
        corr = correlation(data["low"], adv40, 5)
        ts_rank2 = ts_rank(corr, 3)
        return (rank1 ** ts_rank2) * -1
