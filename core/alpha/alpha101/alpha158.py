"""Real WorldQuant Alpha101 formula — Momentum alpha158: ((high - SMA(close, 15, 2)) - (low - SMA(close, 15, 2))) / close"""
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
class Alpha158(AlphaFactor):
    """Momentum alpha158: ((high - SMA(close, 15, 2)) - (low - SMA(close, 15, 2))) / close"""

    @property
    def name(self) -> str:
        return "alpha158"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha158: ((high - SMA(close, 15, 2)) - (low - SMA(close, 15, 2))) / close"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        sma_close = data["close"].ewm(alpha=2/16, adjust=False).mean()
        high_dev = data["high"] - sma_close
        low_dev = data["low"] - sma_close
        return (high_dev - low_dev) / (data["close"] + 1e-8)
