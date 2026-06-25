"""Real WorldQuant Alpha101 formula — Momentum alpha138: (rank(decay_linear(delta(((low * 0.7 + vwap * 0.3)), 3), 20)) - ts_rank(decay_linear(ts_rank(correlation(ts_rank(low, 8), ts_rank(mean(volume, 60), 17), 5), 19), 16)) * -1"""
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
class Alpha138(AlphaFactor):
    """Momentum alpha138: (rank(decay_linear(delta(((low * 0.7 + vwap * 0.3)), 3), 20)) - ts_rank(decay_linear(ts_rank(correlation(ts_rank(low, 8), ts_rank(mean(volume, 60), 17), 5), 19), 16)) * -1"""

    @property
    def name(self) -> str:
        return "alpha138"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha138: (rank(decay_linear(delta(((low * 0.7 + vwap * 0.3)), 3), 20)) - ts_rank(decay_linear(ts_rank(correlation(ts_rank(low, 8), ts_rank(mean(volume, 60), 17), 5), 19), 16)) * -1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Calculate vwap if not available
        if "vwap" in data.columns:
            vwap = data["vwap"]
        else:
            vwap = (data["high"] + data["low"] + data["close"]) / 3

        # First term
        blended = data["low"] * 0.7 + vwap * 0.3
        delta_blended = delta(blended, 3)
        decay_delta = decay_linear(delta_blended, 20)
        rank_decay1 = rank(decay_delta)

        # Second term
        ts_rank_low = ts_rank(data["low"], 8)
        ts_rank_vol = ts_rank(ts_mean(data["volume"], 60), 17)
        corr = correlation(ts_rank_low, ts_rank_vol, 5)
        ts_rank_corr = ts_rank(corr, 19)
        decay_ts = decay_linear(ts_rank_corr, 16)
        ts_rank_decay = ts_rank(decay_ts, 3)

        return (rank_decay1 - ts_rank_decay) * -1
