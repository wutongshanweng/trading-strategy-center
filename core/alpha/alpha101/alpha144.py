"""Real WorldQuant Alpha101 formula — Momentum alpha144: mean(|close / delay(close, 1) - 1| / amount, 20) for down days only"""
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
class Alpha144(AlphaFactor):
    """Momentum alpha144: mean(|close / delay(close, 1) - 1| / amount, 20) for down days only"""

    @property
    def name(self) -> str:
        return "alpha144"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha144: mean(|close / delay(close, 1) - 1| / amount, 20) for down days only"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        returns = np.abs(data["close"].pct_change())
        if "amount" in data.columns:
            amount = data["amount"]
        else:
            amount = data["volume"] * data["close"]

        # Filter for down days only (negative returns)
        down = data["close"] < delay(data["close"], 1)
        vol_adjusted = returns / (amount + 1e-8)
        vol_adjusted[~down] = np.nan
        return vol_adjusted.rolling(20, min_periods=10).mean()
