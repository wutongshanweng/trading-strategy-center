"""Real WorldQuant Alpha101 formula — Momentum alpha111: SMA(volume * (close - low - (high - close)) / (high - low), 11, 2) - SMA(volume * (close - low - (high - close)) / (high - low), 4, 2)"""
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
class Alpha111(AlphaFactor):
    """Momentum alpha111: SMA(volume * (close - low - (high - close)) / (high - low), 11, 2) - SMA(volume * (close - low - (high - close)) / (high - low), 4, 2)"""

    @property
    def name(self) -> str:
        return "alpha111"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha111: SMA(volume * (close - low - (high - close)) / (high - low), 11, 2) - SMA(volume * (close - low - (high - close)) / (high - low), 4, 2)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Money flow indicator: volume * (close - low - (high - close)) / (high - low)
        hl_range = data["high"] - data["low"]
        mf = data["volume"] * (2 * data["close"] - data["low"] - data["high"]) / (hl_range + 1e-8)
        sma11 = mf.ewm(alpha=2/12, adjust=False).mean()
        sma4 = mf.ewm(alpha=2/5, adjust=False).mean()
        return sma11 - sma4
