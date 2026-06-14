"""Real WorldQuant Alpha101 formula — Alpha084: pow(ts_rank(vwap - ts_max(vwap, 15), 21), delta(close, 5))"""
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
class Alpha084(AlphaFactor):
    """Alpha084: pow(ts_rank(vwap - ts_max(vwap, 15), 21), delta(close, 5))"""

    @property
    def name(self) -> str:
        return "alpha084"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha084: pow(ts_rank(vwap - ts_max(vwap, 15), 21), delta(close, 5))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        base = ts_rank(vwap - ts_max(vwap, 15), 21)
        exp = delta(data["close"], 5)
        return base ** exp
