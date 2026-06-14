"""Real WorldQuant Alpha101 formula — Alpha087: Volume-price momentum composite"""
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
class Alpha087(AlphaFactor):
    """Alpha087: Volume-price momentum composite"""

    @property
    def name(self) -> str:
        return "alpha087"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha087: Volume-price momentum composite"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        c, v = data["close"], data["volume"]
        ret = c.pct_change(5)
        return rank(ret) * ts_rank(v, 10) + correlation(c, v, 10)
