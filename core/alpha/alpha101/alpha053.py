"""Real WorldQuant Alpha101 formula — Alpha053: (-1 * delta((((close - low) - (high - close)) / (close - low)), 9))"""
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
class Alpha053(AlphaFactor):
    """Alpha053: (-1 * delta((((close - low) - (high - close)) / (close - low)), 9))"""

    @property
    def name(self) -> str:
        return "alpha053"

    @property
    def category(self) -> str:
        return "price_structure"

    @property
    def description(self) -> str:
        return "Alpha053: (-1 * delta((((close - low) - (high - close)) / (close - low)), 9))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        divisor = (data["close"] - data["low"]).replace(0, 1e-8)
        inner = ((data["close"] - data["low"]) - (data["high"] - data["close"])) / divisor
        return -1 * delta(inner, 9)
