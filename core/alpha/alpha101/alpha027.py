"""Real WorldQuant Alpha101 formula — Alpha027: ((0.5 < rank(sum(correlation(rank(volume), rank(close), 6), 2))) ? (-1 * rank(delta(close, 5))) : 1)"""
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
class Alpha027(AlphaFactor):
    """Alpha027: ((0.5 < rank(sum(correlation(rank(volume), rank(close), 6), 2))) ? (-1 * rank(delta(close, 5))) : 1)"""

    @property
    def name(self) -> str:
        return "alpha027"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha027: ((0.5 < rank(sum(correlation(rank(volume), rank(close), 6), 2))) ? (-1 * rank(delta(close, 5))) : 1)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        corr6 = correlation(rank(data["volume"]), rank(data["close"]), 6)
        sum2 = corr6.rolling(2).sum()
        cond = rank(sum2) > 0.5
        dc5 = -1 * rank(delta(data["close"], 5))
        return pd.Series(np.where(cond, dc5, 1.0), index=data.index)
