"""Real WorldQuant Alpha101 formula — Momentum alpha108: ((rank((high - min(high, 2)))) ** rank(correlation(vwap, mean(volume, 120), 6))) * -1"""
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
class Alpha108(AlphaFactor):
    """Momentum alpha108: ((rank((high - min(high, 2)))) ** rank(correlation(vwap, mean(volume, 120), 6))) * -1"""

    @property
    def name(self) -> str:
        return "alpha108"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha108: ((rank((high - min(high, 2)))) ** rank(correlation(vwap, mean(volume, 120), 6))) * -1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Calculate vwap if not available
        if "vwap" in data.columns:
            vwap = data["vwap"]
        else:
            vwap = (data["high"] + data["low"] + data["close"]) / 3

        min_high = ts_min(data["high"], 2)
        rank_high = rank(data["high"] - min_high)
        mean_vol = ts_mean(data["volume"], 120)
        corr_vwap_vol = correlation(vwap, mean_vol, 6)
        rank_corr = rank(corr_vwap_vol)
        return (rank_high ** rank_corr) * -1
