"""Real WorldQuant Alpha101 formula — alpha045"""
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
class Alpha045_en(AlphaFactor):
    """alpha045: -1*((rank(((sum(delay(close,5),20)/20))*correlation(close,volume,2))*rank(correlation(sum(close,5),sum(close,20),2))))"""

    @property
    def name(self) -> str:
        return "alpha_en_045"

    @property
    def category(self) -> str:
        return "correlation"

    @property
    def description(self) -> str:
        return "-1*((rank(((sum(delay(close,5),20)/20))*correlation(close,volume,2))*rank(correlation(sum(close,5),sum(close,20),2))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        delay_close_5 = delay(data["close"], 5)
        avg_delay = ts_sum(delay_close_5, 20) / 20
        corr1 = correlation(data["close"], data["volume"], 2)
        rank1 = rank(avg_delay * corr1)
        sum_close_5 = ts_sum(data["close"], 5)
        sum_close_20 = ts_sum(data["close"], 20)
        corr2 = correlation(sum_close_5, sum_close_20, 2)
        rank2 = rank(corr2)
        return -1 * rank1 * rank2
