"""Real WorldQuant Alpha101 formula — alpha056"""
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
class Alpha056_en(AlphaFactor):
    """alpha056: 0-(1*(rank((sum(returns,10)/sum(sum(returns,2),3)))*rank((returns))))"""

    @property
    def name(self) -> str:
        return "alpha_en_056"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "0-(1*(rank((sum(returns,10)/sum(sum(returns,2),3)))*rank((returns))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        returns = data["close"].pct_change()
        sum_ret_10 = ts_sum(returns, 10)
        sum_ret_2 = ts_sum(returns, 2)
        sum_sum_ret = ts_sum(sum_ret_2, 3)
        ratio = sum_ret_10 / (sum_sum_ret + 1e-9)
        rank_ratio = rank(ratio)
        rank_ret = rank(returns)
        return -1 * rank_ratio * rank_ret
