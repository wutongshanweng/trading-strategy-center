"""Real WorldQuant Alpha101 formula — Momentum alpha162: (rsi12 - min(rsi12, 12)) / (max(rsi12, 12) - min(rsi12, 12))"""
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
class Alpha162(AlphaFactor):
    """Momentum alpha162: (rsi12 - min(rsi12, 12)) / (max(rsi12, 12) - min(rsi12, 12))"""

    @property
    def name(self) -> str:
        return "alpha162"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha162: (rsi12 - min(rsi12, 12)) / (max(rsi12, 12) - min(rsi12, 12))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Calculate RSI-12
        returns = data["close"].diff()
        gain = returns.clip(lower=0)
        loss = (-returns).clip(lower=0)
        avg_gain = gain.ewm(alpha=1/12, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/12, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-8)
        rsi = 100 - (100 / (1 + rs))

        # Stochastic of RSI
        min_rsi = ts_min(rsi, 12)
        max_rsi = ts_max(rsi, 12)
        return (rsi - min_rsi) / (max_rsi - min_rsi + 1e-8)
