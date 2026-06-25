"""Real WorldQuant Alpha101 formula — Momentum alpha165: (MAX(SUM(close - mean(close, 48), 48)) - MIN(SUM(close - mean(close, 48), 48))) / std(close, 48)"""
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
class Alpha165(AlphaFactor):
    """Momentum alpha165: (MAX(SUM(close - mean(close, 48), 48)) - MIN(SUM(close - mean(close, 48), 48))) / std(close, 48)"""

    @property
    def name(self) -> str:
        return "alpha165"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha165: (MAX(SUM(close - mean(close, 48), 48)) - MIN(SUM(close - mean(close, 48), 48))) / std(close, 48)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        mean_close = ts_mean(data["close"], 48)
        diff = data["close"] - mean_close
        cumsum = ts_sum(diff, 48)
        max_cum = cumsum.rolling(48, min_periods=48).max()
        min_cum = cumsum.rolling(48, min_periods=48).min()
        std_close = ts_std(data["close"], 48)
        return (max_cum - min_cum) / (std_close + 1e-8)
