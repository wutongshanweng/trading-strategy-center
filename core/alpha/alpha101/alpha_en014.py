"""Real WorldQuant Alpha101 formula — alpha014"""
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
class Alpha014_en(AlphaFactor):
    """alpha014: (-1*rank(delta(returns,3)))*correlation(open,volume,10)"""

    @property
    def name(self) -> str:
        return "alpha_en_014"

    @property
    def category(self) -> str:
        return "correlation"

    @property
    def description(self) -> str:
        return "(-1*rank(delta(returns,3)))*correlation(open,volume,10)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        returns = data["close"].pct_change()
        delta_ret = delta(returns, 3)
        rank_delta = -1 * rank(delta_ret)
        corr = correlation(data["open"], data["volume"], 10)
        return rank_delta * corr
