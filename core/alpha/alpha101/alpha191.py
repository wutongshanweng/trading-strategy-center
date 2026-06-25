"""Real WorldQuant Alpha101 formula — Momentum alpha191: corr(mean(volume, 20), low, 5) + ((high + low) / 2) - close"""
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
class Alpha191(AlphaFactor):
    """Momentum alpha191: corr(mean(volume, 20), low, 5) + ((high + low) / 2) - close"""

    @property
    def name(self) -> str:
        return "alpha191"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha191: corr(mean(volume, 20), low, 5) + ((high + low) / 2) - close"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        mean_vol = ts_mean(data["volume"], 20)
        corr = correlation(mean_vol, data["low"], 5)
        mid = (data["high"] + data["low"]) / 2
        return corr + mid - data["close"]
