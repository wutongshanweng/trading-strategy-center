"""Real WorldQuant Alpha101 formula — Momentum alpha160: SMA((close <= delay(close, 1)) * std(close, 20), 20, 1)"""
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
class Alpha160(AlphaFactor):
    """Momentum alpha160: SMA((close <= delay(close, 1)) * std(close, 20), 20, 1)"""

    @property
    def name(self) -> str:
        return "alpha160"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha160: SMA((close <= delay(close, 1)) * std(close, 20), 20, 1)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        down = (data["close"] <= delay(data["close"], 1)).astype(float)
        std_close = ts_std(data["close"], 20)
        filtered = down * std_close
        return filtered.ewm(alpha=1/21, adjust=False).mean()
