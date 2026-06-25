"""Real WorldQuant Alpha101 formula — Momentum alpha128: 100 / (1 + SUM((close > delay(close, 1)) * volume * close, 14) / SUM((close < delay(close, 1)) * volume * close, 14))"""
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
class Alpha128(AlphaFactor):
    """Momentum alpha128: 100 / (1 + SUM((close > delay(close, 1)) * volume * close, 14) / SUM((close < delay(close, 1)) * volume * close, 14))"""

    @property
    def name(self) -> str:
        return "alpha128"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha128: 100 / (1 + SUM((close > delay(close, 1)) * volume * close, 14) / SUM((close < delay(close, 1)) * volume * close, 14))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        d_close = delay(data["close"], 1)
        up = (data["close"] > d_close).astype(float) * data["volume"] * data["close"]
        down = (data["close"] < d_close).astype(float) * data["volume"] * data["close"]
        sum_up = ts_sum(up, 14)
        sum_down = ts_sum(down, 14)
        return 100 / (1 + sum_up / (sum_down + 1e-8))
