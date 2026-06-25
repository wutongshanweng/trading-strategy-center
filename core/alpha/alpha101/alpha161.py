"""Real WorldQuant Alpha101 formula — Momentum alpha161: mean(MAX(MAX((high - low), ABS(delay(close, 1) - high)), ABS(delay(close, 1) - low)), 12)"""
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
class Alpha161(AlphaFactor):
    """Momentum alpha161: mean(MAX(MAX((high - low), ABS(delay(close, 1) - high)), ABS(delay(close, 1) - low)), 12)"""

    @property
    def name(self) -> str:
        return "alpha161"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha161: mean(MAX(MAX((high - low), ABS(delay(close, 1) - high)), ABS(delay(close, 1) - low)), 12)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        d_close = delay(data["close"], 1)
        hl = data["high"] - data["low"]
        abs1 = np.abs(d_close - data["high"])
        abs2 = np.abs(d_close - data["low"])
        inner = np.maximum(np.maximum(hl, abs1), abs2)
        return ts_mean(inner, 12)
