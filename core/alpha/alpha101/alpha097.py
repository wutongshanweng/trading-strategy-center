"""Real WorldQuant Alpha101 formula — Alpha097: Volume-weighted return momentum"""
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
class Alpha097(AlphaFactor):
    """Alpha097: Volume-weighted return momentum"""

    @property
    def name(self) -> str:
        return "alpha097"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha097: Volume-weighted return momentum"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        c, v = data["close"], data["volume"]
        ret = c.pct_change()
        return rank(ret) * ts_rank(v, 20) - correlation(c, v, 10)
