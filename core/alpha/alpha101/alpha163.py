"""Real WorldQuant Alpha101 formula — Momentum alpha163: rank((((-1 * returns) * mean(volume, 20)) * vwap) * (high - close))"""
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
class Alpha163(AlphaFactor):
    """Momentum alpha163: rank((((-1 * returns) * mean(volume, 20)) * vwap) * (high - close))"""

    @property
    def name(self) -> str:
        return "alpha163"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha163: rank((((-1 * returns) * mean(volume, 20)) * vwap) * (high - close))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Calculate vwap if not available
        if "vwap" in data.columns:
            vwap = data["vwap"]
        else:
            vwap = (data["high"] + data["low"] + data["close"]) / 3

        returns = data["close"].pct_change()
        mean_vol = ts_mean(data["volume"], 20)
        inner = (-1 * returns) * mean_vol * vwap * (data["high"] - data["close"])
        return rank(inner)
