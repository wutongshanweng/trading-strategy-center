"""Real WorldQuant Alpha101 formula — Momentum alpha167: SUM((close > delay(close, 1)) * (close - delay(close, 1)), 12)"""
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
class Alpha167(AlphaFactor):
    """Momentum alpha167: SUM((close > delay(close, 1)) * (close - delay(close, 1)), 12)"""

    @property
    def name(self) -> str:
        return "alpha167"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha167: SUM((close > delay(close, 1)) * (close - delay(close, 1)), 12)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        d_close = delay(data["close"], 1)
        up = (data["close"] > d_close).astype(float)
        gain = (data["close"] - d_close) * up
        return ts_sum(gain, 12)
