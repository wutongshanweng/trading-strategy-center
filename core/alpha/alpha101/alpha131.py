"""Real WorldQuant Alpha101 formula — Momentum alpha131: rank(delta(vwap, 1)) ** ts_rank(correlation(close, mean(volume, 50), 18), 18)"""
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
class Alpha131(AlphaFactor):
    """Momentum alpha131: rank(delta(vwap, 1)) ** ts_rank(correlation(close, mean(volume, 50), 18), 18)"""

    @property
    def name(self) -> str:
        return "alpha131"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha131: rank(delta(vwap, 1)) ** ts_rank(correlation(close, mean(volume, 50), 18), 18)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Calculate vwap if not available
        if "vwap" in data.columns:
            vwap = data["vwap"]
        else:
            vwap = (data["high"] + data["low"] + data["close"]) / 3

        rank_delta_vwap = rank(delta(vwap, 1))
        corr = correlation(data["close"], ts_mean(data["volume"], 50), 18)
        ts_rank_corr = ts_rank(corr, 18)
        return rank_delta_vwap ** ts_rank_corr
