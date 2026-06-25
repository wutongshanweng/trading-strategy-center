"""Real WorldQuant Alpha101 formula — Momentum alpha183: (MAX(SUM(close - mean(close, 24), 24)) - MIN(SUM(close - mean(close, 24), 24))) / std(close, 24)"""
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
class Alpha183(AlphaFactor):
    """Momentum alpha183: (MAX(SUM(close - mean(close, 24), 24)) - MIN(SUM(close - mean(close, 24), 24))) / std(close, 24)"""

    @property
    def name(self) -> str:
        return "alpha183"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha183: (MAX(SUM(close - mean(close, 24), 24)) - MIN(SUM(close - mean(close, 24), 24))) / std(close, 24)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        mean_close = ts_mean(data["close"], 24)
        diff = data["close"] - mean_close
        cumsum = ts_sum(diff, 24)
        max_cum = cumsum.rolling(24, min_periods=24).max()
        min_cum = cumsum.rolling(24, min_periods=24).min()
        std_close = ts_std(data["close"], 24)
        return (max_cum - min_cum) / (std_close + 1e-8)
