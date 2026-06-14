"""Real WorldQuant Alpha101 formula — Alpha082: Momentum correlation composite"""
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
class Alpha082(AlphaFactor):
    """Alpha082: Momentum correlation composite"""

    @property
    def name(self) -> str:
        return "alpha082"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha082: Momentum correlation composite"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        c, v = data["close"], data["volume"]
        return rank(delta(c, 5)) * ts_rank(correlation(c, v, 10), 5)
