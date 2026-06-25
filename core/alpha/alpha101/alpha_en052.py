"""Real WorldQuant Alpha101 formula — alpha052"""
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
class Alpha052_en(AlphaFactor):
    """alpha052: ((((-1*ts_min(low,5))+delay(ts_min(low,5),5))*rank(((sum(returns,240)-sum(returns,20))/220)))*ts_rank(volume,5))"""

    @property
    def name(self) -> str:
        return "alpha_en_052"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "((( (-1*ts_min(low,5))+delay(ts_min(low,5),5))*rank(((sum(returns,240)-sum(returns,20))/220)))*ts_rank(volume,5))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        returns = data["close"].pct_change()
        ts_min_low = ts_min(data["low"], 5)
        delayed_min_low = delay(ts_min_low, 5)
        sum_ret_240 = ts_sum(returns, 240)
        sum_ret_20 = ts_sum(returns, 20)
        momentum_ratio = (sum_ret_240 - sum_ret_20) / 220
        ts_rank_vol = ts_rank(data["volume"], 5)
        return (-1 * ts_min_low + delayed_min_low) * rank(momentum_ratio) * ts_rank_vol
