"""Real WorldQuant Alpha101 formula — Volatility alpha109: SMA(high-low, 10, 2) / SMA(SMA(high-low, 10, 2), 10, 2)"""
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
class Alpha109(AlphaFactor):
    """Volatility alpha109: SMA(high-low, 10, 2) / SMA(SMA(high-low, 10, 2), 10, 2)"""

    @property
    def name(self) -> str:
        return "alpha109"

    @property
    def category(self) -> str:
        return "volatility"

    @property
    def description(self) -> str:
        return "Volatility alpha109: SMA(high-low, 10, 2) / SMA(SMA(high-low, 10, 2), 10, 2)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        high_low = data["high"] - data["low"]
        sma1 = high_low.ewm(alpha=2/11, adjust=False).mean()
        sma2 = sma1.ewm(alpha=2/11, adjust=False).mean()
        return sma1 / (sma2 + 1e-8)
