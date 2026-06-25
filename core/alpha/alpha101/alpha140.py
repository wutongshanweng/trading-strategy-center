"""Real WorldQuant Alpha101 formula — Momentum alpha140: min(rank(decay_linear(((rank(open) + rank(low)) - (rank(high) + rank(close))), 8)), ts_rank(decay_linear(correlation(ts_rank(close, 8), ts_rank(mean(volume, 60), 20), 8), 7), 3))"""
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
class Alpha140(AlphaFactor):
    """Momentum alpha140: min(rank(decay_linear(((rank(open) + rank(low)) - (rank(high) + rank(close))), 8)), ts_rank(decay_linear(correlation(ts_rank(close, 8), ts_rank(mean(volume, 60), 20), 8), 7), 3))"""

    @property
    def name(self) -> str:
        return "alpha140"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha140: min(rank(decay_linear(((rank(open) + rank(low)) - (rank(high) + rank(close))), 8)), ts_rank(decay_linear(correlation(ts_rank(close, 8), ts_rank(mean(volume, 60), 20), 8), 7), 3))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # First term
        inner = (rank(data["open"]) + rank(data["low"])) - (rank(data["high"]) + rank(data["close"]))
        decay_inner = decay_linear(inner, 8)
        rank_decay = rank(decay_inner)

        # Second term
        ts_rank_close = ts_rank(data["close"], 8)
        ts_rank_vol = ts_rank(ts_mean(data["volume"], 60), 20)
        corr = correlation(ts_rank_close, ts_rank_vol, 8)
        decay_corr = decay_linear(corr, 7)
        ts_rank_decay = ts_rank(decay_corr, 3)

        return np.minimum(rank_decay, ts_rank_decay)
