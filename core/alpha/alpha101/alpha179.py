"""Real WorldQuant Alpha101 formula — Momentum alpha179: rank(correlation(vwap, volume, 4)) * rank(correlation(rank(low), rank(mean(volume, 50)), 12))"""
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
class Alpha179(AlphaFactor):
    """Momentum alpha179: rank(correlation(vwap, volume, 4)) * rank(correlation(rank(low), rank(mean(volume, 50)), 12))"""

    @property
    def name(self) -> str:
        return "alpha179"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha179: rank(correlation(vwap, volume, 4)) * rank(correlation(rank(low), rank(mean(volume, 50)), 12))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Calculate vwap if not available
        if "vwap" in data.columns:
            vwap = data["vwap"]
        else:
            vwap = (data["high"] + data["low"] + data["close"]) / 3

        corr1 = correlation(vwap, data["volume"], 4)
        rank_corr1 = rank(corr1)

        rank_low = rank(data["low"])
        rank_mean_vol = rank(ts_mean(data["volume"], 50))
        corr2 = correlation(rank_low, rank_mean_vol, 12)
        rank_corr2 = rank(corr2)

        return rank_corr1 * rank_corr2
