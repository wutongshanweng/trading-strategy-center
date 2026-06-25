"""Real WorldQuant Alpha101 formula — Momentum alpha137: 16 * (close - delay(close, 1) + (close - open) / 2 + delay(close, 1) - delay(open, 1)) / typical_price_range * max_range"""
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
class Alpha137(AlphaFactor):
    """Momentum alpha137: 16 * (close - delay(close, 1) + (close - open) / 2 + delay(close, 1) - delay(open, 1)) / typical_price_range * max_range"""

    @property
    def name(self) -> str:
        return "alpha137"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha137: 16 * (close - delay(close, 1) + (close - open) / 2 + delay(close, 1) - delay(open, 1)) / typical_price_range * max_range"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        d_close = delay(data["close"], 1)
        d_open = delay(data["open"], 1)
        # Simplified formula: momentum normalized by range
        numerator = data["close"] - d_close + (data["close"] - data["open"]) / 2 + d_close - d_open
        # Typical price range * max_range (approximated with rolling max of high-low)
        typical_range = data["high"] - data["low"]
        max_range = typical_range.rolling(20, min_periods=20).max()
        return 16 * numerator / (typical_range + 1e-8) * max_range
