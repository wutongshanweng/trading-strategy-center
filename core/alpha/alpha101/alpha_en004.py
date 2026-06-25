"""Real WorldQuant Alpha101 formula — alpha004"""
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
class Alpha004_en(AlphaFactor):
    """alpha004: -1*ts_rank(rank(low),9)"""

    @property
    def name(self) -> str:
        return "alpha_en_004"

    @property
    def category(self) -> str:
        return "time_series"

    @property
    def description(self) -> str:
        return "-1*ts_rank(rank(low),9)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        rank_low = rank(data["low"])
        ts_rank_val = ts_rank(rank_low, 9)
        return -1 * ts_rank_val
