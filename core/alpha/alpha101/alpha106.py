"""Real WorldQuant Alpha101 formula — Momentum alpha106: close - delay(close, 20)"""
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
class Alpha106(AlphaFactor):
    """Momentum alpha106: close - delay(close, 20) — price change over 20 periods"""

    @property
    def name(self) -> str:
        return "alpha106"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha106: close - delay(close, 20) — price change over 20 periods"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return data["close"] - delay(data["close"], 20)
