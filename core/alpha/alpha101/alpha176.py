"""Real WorldQuant Alpha101 formula — Momentum alpha176: correlation(rank((close - tsmin(low, 12)) / (tsmax(high, 12) - tsmin(low, 12))), rank(volume), 6)"""
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
class Alpha176(AlphaFactor):
    """Momentum alpha176: correlation(rank((close - tsmin(low, 12)) / (tsmax(high, 12) - tsmin(low, 12))), rank(volume), 6)"""

    @property
    def name(self) -> str:
        return "alpha176"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha176: correlation(rank((close - tsmin(low, 12)) / (tsmax(high, 12) - tsmin(low, 12))), rank(volume), 6)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Stochastic-like value
        min_low = ts_min(data["low"], 12)
        max_high = ts_max(data["high"], 12)
        stoch = (data["close"] - min_low) / (max_high - min_low + 1e-8)
        rank_stoch = rank(stoch)
        rank_vol = rank(data["volume"])
        return correlation(rank_stoch, rank_vol, 6)
