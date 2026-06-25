"""Real WorldQuant Alpha101 formula — Momentum alpha113: -1 * (rank(sum(delay(close, 5), 20) / 20) * correlation(close, volume, 2)) * rank(correlation(sum(close, 5), sum(close, 20), 2))"""
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
class Alpha113(AlphaFactor):
    """Momentum alpha113: -1 * (rank(sum(delay(close, 5), 20) / 20) * correlation(close, volume, 2)) * rank(correlation(sum(close, 5), sum(close, 20), 2))"""

    @property
    def name(self) -> str:
        return "alpha113"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha113: -1 * (rank(sum(delay(close, 5), 20) / 20) * correlation(close, volume, 2)) * rank(correlation(sum(close, 5), sum(close, 20), 2))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        d_close_5 = ts_sum(delay(data["close"], 5), 20) / 20
        rank_dc = rank(d_close_5)
        corr1 = correlation(data["close"], data["volume"], 2)
        sum_close_5 = ts_sum(data["close"], 5)
        sum_close_20 = ts_sum(data["close"], 20)
        corr2 = correlation(sum_close_5, sum_close_20, 2)
        rank_corr2 = rank(corr2)
        return -1 * rank_dc * corr1 * rank_corr2
