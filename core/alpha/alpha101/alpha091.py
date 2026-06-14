"""Real WorldQuant Alpha101 formula — Alpha091: Return-volume correlation composite"""
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
class Alpha091(AlphaFactor):
    """Alpha091: Return-volume correlation composite"""

    @property
    def name(self) -> str:
        return "alpha091"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha091: Return-volume correlation composite"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        ret = data["close"].pct_change()
        return rank(correlation(ret, data["volume"], 10)) * ts_rank(data["close"], 10)
