"""Real WorldQuant Alpha101 formula — Momentum alpha125: rank(decay_linear(correlation(vwap, mean(volume, 80), 17), 20)) / rank(decay_linear(delta((close * 0.5 + vwap * 0.5), 3), 16))"""
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
class Alpha125(AlphaFactor):
    """Momentum alpha125: rank(decay_linear(correlation(vwap, mean(volume, 80), 17), 20)) / rank(decay_linear(delta((close * 0.5 + vwap * 0.5), 3), 16))"""

    @property
    def name(self) -> str:
        return "alpha125"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha125: rank(decay_linear(correlation(vwap, mean(volume, 80), 17), 20)) / rank(decay_linear(delta((close * 0.5 + vwap * 0.5), 3), 16))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Calculate vwap if not available
        if "vwap" in data.columns:
            vwap = data["vwap"]
        else:
            vwap = (data["high"] + data["low"] + data["close"]) / 3

        # First term
        corr = correlation(vwap, ts_mean(data["volume"], 80), 17)
        decay_corr = decay_linear(corr, 20)
        rank_decay1 = rank(decay_corr)

        # Second term
        mid = data["close"] * 0.5 + vwap * 0.5
        delta_mid = delta(mid, 3)
        decay_delta = decay_linear(delta_mid, 16)
        rank_decay2 = rank(decay_delta)

        return rank_decay1 / (rank_decay2 + 1e-8)
