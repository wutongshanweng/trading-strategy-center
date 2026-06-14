"""Real WorldQuant Alpha101 formula — Alpha083: (rank(delay((high - low) / (ts_sum(close, 5) / 5), 2)) * rank(rank(volume))) / ((high - low) / (ts_sum(close, 5) / 5) / (vwap - close))"""
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
class Alpha083(AlphaFactor):
    """Alpha083: (rank(delay((high - low) / (ts_sum(close, 5) / 5), 2)) * rank(rank(volume))) / ((high - low) / (ts_sum(close, 5) / 5) / (vwap - close))"""

    @property
    def name(self) -> str:
        return "alpha083"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha083: (rank(delay((high - low) / (ts_sum(close, 5) / 5), 2)) * rank(rank(volume))) / ((high - low) / (ts_sum(close, 5) / 5) / (vwap - close))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        hl_range = (data["high"] - data["low"])
        avg_close = ts_sum(data["close"], 5) / 5
        inner = hl_range / avg_close
        numerator = rank(delay(inner, 2)) * rank(rank(data["volume"]))
        denominator = inner / (vwap - data["close"] + 1e-8)
        return numerator / denominator
