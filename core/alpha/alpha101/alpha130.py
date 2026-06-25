"""Real WorldQuant Alpha101 formula — Momentum alpha130: rank(decay_linear(correlation((high + low) / 2, mean(volume, 40), 9), 10)) / rank(decay_linear(correlation(rank(vwap), rank(volume), 7), 3))"""
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
class Alpha130(AlphaFactor):
    """Momentum alpha130: rank(decay_linear(correlation((high + low) / 2, mean(volume, 40), 9), 10)) / rank(decay_linear(correlation(rank(vwap), rank(volume), 7), 3))"""

    @property
    def name(self) -> str:
        return "alpha130"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha130: rank(decay_linear(correlation((high + low) / 2, mean(volume, 40), 9), 10)) / rank(decay_linear(correlation(rank(vwap), rank(volume), 7), 3))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Calculate vwap if not available
        if "vwap" in data.columns:
            vwap = data["vwap"]
        else:
            vwap = (data["high"] + data["low"] + data["close"]) / 3

        # First term
        hl = (data["high"] + data["low"]) / 2
        corr1 = correlation(hl, ts_mean(data["volume"], 40), 9)
        decay_corr1 = decay_linear(corr1, 10)
        rank_decay1 = rank(decay_corr1)

        # Second term
        corr2 = correlation(rank(vwap), rank(data["volume"]), 7)
        decay_corr2 = decay_linear(corr2, 3)
        rank_decay2 = rank(decay_corr2)

        return rank_decay1 / (rank_decay2 + 1e-8)
