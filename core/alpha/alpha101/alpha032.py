"""Real WorldQuant Alpha101 formula — Alpha032: (scale(((sma(close, 7) / 7) - close)) + (20 * scale(correlation(vwap, delay(close, 5), 230))))"""
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
class Alpha032(AlphaFactor):
    """Alpha032: (scale(((sma(close, 7) / 7) - close)) + (20 * scale(correlation(vwap, delay(close, 5), 230))))"""

    @property
    def name(self) -> str:
        return "alpha032"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha032: (scale(((sma(close, 7) / 7) - close)) + (20 * scale(correlation(vwap, delay(close, 5), 230))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        term1 = scale(((data["close"].rolling(7).mean() / 7) - data["close"]))
        w = min(230, len(data) - 1)
        term2 = 20 * scale(correlation(vwap, delay(data["close"], 5), w))
        return term1 + term2
