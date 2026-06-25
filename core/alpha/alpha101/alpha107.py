"""Real WorldQuant Alpha101 formula — Momentum alpha107: (-1 * rank(((open - delay(high, 1)) * (open - delay(close, 1)) * (open - delay(low, 1)))))"""
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
class Alpha107(AlphaFactor):
    """Momentum alpha107: (-1 * rank(((open - delay(high, 1)) * (open - delay(close, 1)) * (open - delay(low, 1)))))"""

    @property
    def name(self) -> str:
        return "alpha107"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha107: (-1 * rank(((open - delay(high, 1)) * (open - delay(close, 1)) * (open - delay(low, 1)))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        d_high = delay(data["high"], 1)
        d_close = delay(data["close"], 1)
        d_low = delay(data["low"], 1)
        inner = (data["open"] - d_high) * (data["open"] - d_close) * (data["open"] - d_low)
        return -1 * rank(inner)
