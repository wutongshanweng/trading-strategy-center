"""Real WorldQuant Alpha101 formula — Momentum alpha171: (-1 * ((low - close) * (open ** 5))) / ((close - high) * (close ** 5))"""
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
class Alpha171(AlphaFactor):
    """Momentum alpha171: (-1 * ((low - close) * (open ** 5))) / ((close - high) * (close ** 5))"""

    @property
    def name(self) -> str:
        return "alpha171"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha171: (-1 * ((low - close) * (open ** 5))) / ((close - high) * (close ** 5))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        numerator = -1 * (data["low"] - data["close"]) * (data["open"] ** 5)
        denominator = (data["close"] - data["high"]) * (data["close"] ** 5 + 1e-8)
        return numerator / (denominator + 1e-8)
