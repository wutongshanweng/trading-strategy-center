"""Real WorldQuant Alpha101 formula — Momentum alpha150: (close + high + low) / 3 * volume"""
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
class Alpha150(AlphaFactor):
    """Momentum alpha150: (close + high + low) / 3 * volume — volume-weighted typical price"""

    @property
    def name(self) -> str:
        return "alpha150"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha150: (close + high + low) / 3 * volume — volume-weighted typical price"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        typical_price = (data["close"] + data["high"] + data["low"]) / 3
        return typical_price * data["volume"]
