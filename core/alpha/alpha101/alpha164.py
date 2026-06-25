"""Real WorldQuant Alpha101 formula — Momentum alpha164: SMA(((close > delay(close, 1)) * 1 / (close - delay(close, 1)) + 1) - min(((high - low) * 100), 1), 13, 2)"""
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
class Alpha164(AlphaFactor):
    """Momentum alpha164: SMA(((close > delay(close, 1)) * 1 / (close - delay(close, 1)) + 1) - min(((high - low) * 100), 1), 13, 2)"""

    @property
    def name(self) -> str:
        return "alpha164"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha164: SMA(((close > delay(close, 1)) * 1 / (close - delay(close, 1)) + 1) - min(((high - low) * 100), 1), 13, 2)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        d_close = delay(data["close"], 1)
        up = data["close"] > d_close
        inv_change = 1 / (data["close"] - d_close + 1e-8)
        term1 = up.astype(float) * inv_change + 1
        hl_scaled = ((data["high"] - data["low"]) * 100).clip(upper=1)
        inner = term1 - hl_scaled
        return inner.ewm(alpha=2/14, adjust=False).mean()
