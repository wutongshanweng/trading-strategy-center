"""Real WorldQuant Alpha101 formula — Momentum alpha156: (max(rank(decay_linear(delta(vwap, 5), 3)), rank(decay_linear(delta(((open * 0.15 + low * 0.85)), 2) / ((open * 0.15 + low * 0.85)) * -1, 3))) * -1"""
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
class Alpha156(AlphaFactor):
    """Momentum alpha156: (max(rank(decay_linear(delta(vwap, 5), 3)), rank(decay_linear(delta(((open * 0.15 + low * 0.85)), 2) / ((open * 0.15 + low * 0.85)) * -1, 3))) * -1"""

    @property
    def name(self) -> str:
        return "alpha156"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha156: (max(rank(decay_linear(delta(vwap, 5), 3)), rank(decay_linear(delta(((open * 0.15 + low * 0.85)), 2) / ((open * 0.15 + low * 0.85)) * -1, 3))) * -1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Calculate vwap if not available
        if "vwap" in data.columns:
            vwap = data["vwap"]
        else:
            vwap = (data["high"] + data["low"] + data["close"]) / 3

        # First term
        delta_vwap = delta(vwap, 5)
        decay_delta1 = decay_linear(delta_vwap, 3)
        rank_decay1 = rank(decay_delta1)

        # Second term
        blended = data["open"] * 0.15 + data["low"] * 0.85
        delta_blended = delta(blended, 2)
        ratio = delta_blended / (blended + 1e-8) * -1
        decay_ratio = decay_linear(ratio, 3)
        rank_decay2 = rank(decay_ratio)

        return np.maximum(rank_decay1, rank_decay2) * -1
