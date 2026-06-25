"""Real WorldQuant Alpha101 formula — Momentum alpha159: vwap - (SMA(vwap, 10, 2) + 2 * SMA((high - low), 10, 2)) — Keltner-like"""
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
class Alpha159(AlphaFactor):
    """Momentum alpha159: vwap - (SMA(vwap, 10, 2) + 2 * SMA((high - low), 10, 2)) — Keltner-like"""

    @property
    def name(self) -> str:
        return "alpha159"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha159: vwap - (SMA(vwap, 10, 2) + 2 * SMA((high - low), 10, 2)) — Keltner-like"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Calculate vwap if not available
        if "vwap" in data.columns:
            vwap = data["vwap"]
        else:
            vwap = (data["high"] + data["low"] + data["close"]) / 3

        sma_vwap = vwap.ewm(alpha=2/11, adjust=False).mean()
        hl_range = data["high"] - data["low"]
        sma_hl = hl_range.ewm(alpha=2/11, adjust=False).mean()
        upper_band = sma_vwap + 2 * sma_hl
        return vwap - upper_band
