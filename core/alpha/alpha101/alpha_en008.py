"""Real WorldQuant Alpha101 formula — alpha008"""
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
class Alpha008_en(AlphaFactor):
    """alpha008: -1*rank((sum(open,5)*sum(returns,5))-delay((sum(open,5)*sum(returns,5)),10))"""

    @property
    def name(self) -> str:
        return "alpha_en_008"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "-1*rank((sum(open,5)*sum(returns,5))-delay((sum(open,5)*sum(returns,5)),10))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        returns = data["close"].pct_change()
        sum_open_5 = ts_sum(data["open"], 5)
        sum_ret_5 = ts_sum(returns, 5)
        product = sum_open_5 * sum_ret_5
        delayed = delay(product, 10)
        result = product - delayed
        return -1 * rank(result)
