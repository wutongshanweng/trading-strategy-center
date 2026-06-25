"""Real WorldQuant Alpha101 formula — Momentum alpha152: SMA(mean(delay(SMA(close / delay(close, 9), 9, 1), 1), 12) - mean(delay(SMA(close / delay(close, 9), 9, 1), 1), 26), 9, 1)"""
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
class Alpha152(AlphaFactor):
    """Momentum alpha152: SMA(mean(delay(SMA(close / delay(close, 9), 9, 1), 1), 12) - mean(delay(SMA(close / delay(close, 9), 9, 1), 1), 26), 9, 1)"""

    @property
    def name(self) -> str:
        return "alpha152"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha152: SMA(mean(delay(SMA(close / delay(close, 9), 9, 1), 1), 12) - mean(delay(SMA(close / delay(close, 9), 9, 1), 1), 26), 9, 1)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Rate of change ratio
        d_close_9 = delay(data["close"], 9)
        ratio = data["close"] / (d_close_9 + 1e-8)
        sma_ratio = ratio.ewm(alpha=2/10, adjust=False).mean()
        delayed_sma = delay(sma_ratio, 1)

        mean_12 = delayed_sma.rolling(12).mean()
        mean_26 = delayed_sma.rolling(26).mean()
        diff = mean_12 - mean_26
        return diff.ewm(alpha=1/10, adjust=False).mean()
