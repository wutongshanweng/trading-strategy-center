"""Real WorldQuant Alpha101 formula — Momentum alpha134: (close - delay(close, 12)) / delay(close, 12) * volume"""
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
class Alpha134(AlphaFactor):
    """Momentum alpha134: (close - delay(close, 12)) / delay(close, 12) * volume"""

    @property
    def name(self) -> str:
        return "alpha134"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha134: (close - delay(close, 12)) / delay(close, 12) * volume"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        d_close = delay(data["close"], 12)
        pct_change = (data["close"] - d_close) / (d_close + 1e-8)
        return pct_change * data["volume"]
