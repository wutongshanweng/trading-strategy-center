"""Real WorldQuant Alpha101 formula — Momentum alpha169: SMA(mean(delay(SMA(close - delay(close, 1), 9, 1), 1), 12) - mean(delay(SMA(close - delay(close, 1), 9, 1), 1), 26), 10, 1)"""
import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .operators import (
    rank, ts_rank, ts_argmax, ts_argmin, ts_sum, ts_product,
    ts_min, ts_max, ts_mean, ts_std, ts_cov, correlation, covariance,
    scale, delay, delta, signedpower, decay_linear, signed_sqrt,
)


@FactorRegistry.register
class Alpha169(AlphaFactor):
    """Momentum alpha169: SMA(mean(delay(SMA(close - delay(close, 1), 9, 1), 1), 12) - mean(delay(SMA(close - delay(close, 1), 9, 1), 1), 26), 10, 1)"""

    @property
    def name(self) -> str:
        return "alpha169"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha169: SMA(mean(delay(SMA(close - delay(close, 1), 9, 1), 1), 12) - mean(delay(SMA(close - delay(close, 1), 9, 1), 1), 26), 10, 1)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Price change
        change = data["close"] - delay(data["close"], 1)
        sma_change = change.ewm(alpha=2/10, adjust=False).mean()
        delayed = delay(sma_change, 1)

        mean_12 = delayed.rolling(12).mean()
        mean_26 = delayed.rolling(26).mean()
        diff = mean_12 - mean_26
        return diff.ewm(alpha=1/11, adjust=False).mean()
