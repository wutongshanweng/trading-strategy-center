"""Real WorldQuant Alpha101 formula — Momentum alpha178: (close - delay(close, 1)) / delay(close, 1) * volume"""
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
class Alpha178(AlphaFactor):
    """Momentum alpha178: (close - delay(close, 1)) / delay(close, 1) * volume"""

    @property
    def name(self) -> str:
        return "alpha178"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha178: (close - delay(close, 1)) / delay(close, 1) * volume"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        returns = data["close"].pct_change()
        return returns * data["volume"]
