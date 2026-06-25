"""Real WorldQuant Alpha101 formula — Volatility alpha127: ((100 * (close - max(close, 12)) / max(close, 12)) ** 2).mean() ** 0.5"""
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
class Alpha127(AlphaFactor):
    """Volatility alpha127: ((100 * (close - max(close, 12)) / max(close, 12)) ** 2).mean() ** 0.5"""

    @property
    def name(self) -> str:
        return "alpha127"

    @property
    def category(self) -> str:
        return "volatility"

    @property
    def description(self) -> str:
        return "Volatility alpha127: ((100 * (close - max(close, 12)) / max(close, 12)) ** 2).mean() ** 0.5"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Rolling max
        max_close = data["close"].rolling(12, min_periods=12).max()
        pct_diff = 100 * (data["close"] - max_close) / (max_close + 1e-8)
        squared = pct_diff ** 2
        return squared.rolling(12, min_periods=12).mean() ** 0.5
