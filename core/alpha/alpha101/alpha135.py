"""Real WorldQuant Alpha101 formula — Momentum alpha135: SMA(delay(close / delay(close, 20), 1), 20, 1)"""
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
class Alpha135(AlphaFactor):
    """Momentum alpha135: SMA(delay(close / delay(close, 20), 1), 20, 1)"""

    @property
    def name(self) -> str:
        return "alpha135"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha135: SMA(delay(close / delay(close, 20), 1), 20, 1)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        d_close_20 = delay(data["close"], 20)
        ratio = data["close"] / (d_close_20 + 1e-8)
        delayed_ratio = delay(ratio, 1)
        return delayed_ratio.ewm(alpha=1/21, adjust=False).mean()
