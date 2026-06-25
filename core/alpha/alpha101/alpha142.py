"""Real WorldQuant Alpha101 formula — Momentum alpha142: ((-1 * rank(ts_rank(close, 10))) * rank(delta(delta(close, 1), 1)) * rank(ts_rank((volume / mean(volume, 20)), 5)))"""
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
class Alpha142(AlphaFactor):
    """Momentum alpha142: ((-1 * rank(ts_rank(close, 10))) * rank(delta(delta(close, 1), 1)) * rank(ts_rank((volume / mean(volume, 20)), 5)))"""

    @property
    def name(self) -> str:
        return "alpha142"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha142: ((-1 * rank(ts_rank(close, 10))) * rank(delta(delta(close, 1), 1)) * rank(ts_rank((volume / mean(volume, 20)), 5)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        ts_rank_close = ts_rank(data["close"], 10)
        delta2 = delta(delta(data["close"], 1), 1)
        vol_ratio = data["volume"] / (ts_mean(data["volume"], 20) + 1e-8)
        ts_rank_vol = ts_rank(vol_ratio, 5)
        return -1 * rank(ts_rank_close) * rank(delta2) * rank(ts_rank_vol)
