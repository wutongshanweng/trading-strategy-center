"""Real WorldQuant Alpha101 formula — Momentum alpha119: rank(decay_linear(correlation(vwap, sum(mean(volume, 5), 26), 5), 7)) - rank(decay_linear(ts_rank(min(correlation(rank(open), rank(mean(volume, 15)), 21), 9), 7), 8))"""
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
class Alpha119(AlphaFactor):
    """Momentum alpha119: rank(decay_linear(correlation(vwap, sum(mean(volume, 5), 26), 5), 7)) - rank(decay_linear(ts_rank(min(correlation(rank(open), rank(mean(volume, 15)), 21), 9), 7), 8))"""

    @property
    def name(self) -> str:
        return "alpha119"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha119: rank(decay_linear(correlation(vwap, sum(mean(volume, 5), 26), 5), 7)) - rank(decay_linear(ts_rank(min(correlation(rank(open), rank(mean(volume, 15)), 21), 9), 7), 8))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Calculate vwap if not available
        if "vwap" in data.columns:
            vwap = data["vwap"]
        else:
            vwap = (data["high"] + data["low"] + data["close"]) / 3

        # First term
        sum_vol_5 = ts_sum(ts_mean(data["volume"], 5), 26)
        corr1 = correlation(vwap, sum_vol_5, 5)
        decay_corr1 = decay_linear(corr1, 7)
        rank_decay1 = rank(decay_corr1)

        # Second term
        rank_open = rank(data["open"])
        rank_mean_vol = rank(ts_mean(data["volume"], 15))
        corr2 = correlation(rank_open, rank_mean_vol, 21)
        min_corr = ts_min(corr2, 9)
        ts_rank_min = ts_rank(min_corr, 7)
        decay_ts = decay_linear(ts_rank_min, 8)
        rank_decay2 = rank(decay_ts)

        return rank_decay1 - rank_decay2
