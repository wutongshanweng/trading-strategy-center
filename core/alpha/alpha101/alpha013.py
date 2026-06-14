"""Real WorldQuant Alpha101 formula — Alpha013: (((rank(delta(high, 1)) + rank(delta(low, 1))) / 2 + rank(delta(close, 1)) + rank(delta(volume, 1))) / 4)"""
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
class Alpha013(AlphaFactor):
    """Alpha013: (((rank(delta(high, 1)) + rank(delta(low, 1))) / 2 + rank(delta(close, 1)) + rank(delta(volume, 1))) / 4)"""

    @property
    def name(self) -> str:
        return "alpha013"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Alpha013: (((rank(delta(high, 1)) + rank(delta(low, 1))) / 2 + rank(delta(close, 1)) + rank(delta(volume, 1))) / 4)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        dh = rank(delta(data["high"], 1))
        dl = rank(delta(data["low"], 1))
        dc = rank(delta(data["close"], 1))
        dv = rank(delta(data["volume"], 1))
        return (dh + dl) / 2 + dc + dv / 4
