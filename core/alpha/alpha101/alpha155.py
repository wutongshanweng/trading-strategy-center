"""Real WorldQuant Alpha101 formula — Momentum alpha155: SMA(volume, 13, 2) - SMA(volume, 27, 2) - SMA(SMA(volume, 13, 2) - SMA(volume, 27, 2), 10, 2)"""
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
class Alpha155(AlphaFactor):
    """Momentum alpha155: SMA(volume, 13, 2) - SMA(volume, 27, 2) - SMA(SMA(volume, 13, 2) - SMA(volume, 27, 2), 10, 2)"""

    @property
    def name(self) -> str:
        return "alpha155"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha155: SMA(volume, 13, 2) - SMA(volume, 27, 2) - SMA(SMA(volume, 13, 2) - SMA(volume, 27, 2), 10, 2)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # MACD-like for volume
        sma_13 = data["volume"].ewm(alpha=2/14, adjust=False).mean()
        sma_27 = data["volume"].ewm(alpha=2/28, adjust=False).mean()
        macd = sma_13 - sma_27
        signal = macd.ewm(alpha=2/11, adjust=False).mean()
        return macd - signal
