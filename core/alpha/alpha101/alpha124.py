"""Real WorldQuant Alpha101 formula — Momentum alpha124: (close - vwap) / decay_linear(rank(tsmax(close, 30)), 2)"""
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
class Alpha124(AlphaFactor):
    """Momentum alpha124: (close - vwap) / decay_linear(rank(tsmax(close, 30)), 2)"""

    @property
    def name(self) -> str:
        return "alpha124"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha124: (close - vwap) / decay_linear(rank(tsmax(close, 30)), 2)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Calculate vwap if not available
        if "vwap" in data.columns:
            vwap = data["vwap"]
        else:
            vwap = (data["high"] + data["low"] + data["close"]) / 3

        tsmax_close = ts_max(data["close"], 30)
        rank_tsmax = rank(tsmax_close)
        decay_rank = decay_linear(rank_tsmax, 2)
        return (data["close"] - vwap) / (decay_rank + 1e-8)
