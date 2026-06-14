"""Real WorldQuant Alpha101 formula — Alpha055: (-1 * correlation(rank(((close - ts_min(low, 12)) / (ts_max(high, 12) - ts_min(low, 12)))), rank(volume), 6))"""
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
class Alpha055(AlphaFactor):
    """Alpha055: (-1 * correlation(rank(((close - ts_min(low, 12)) / (ts_max(high, 12) - ts_min(low, 12)))), rank(volume), 6))"""

    @property
    def name(self) -> str:
        return "alpha055"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha055: (-1 * correlation(rank(((close - ts_min(low, 12)) / (ts_max(high, 12) - ts_min(low, 12)))), rank(volume), 6))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        divisor = (ts_max(data["high"], 12) - ts_min(data["low"], 12)).replace(0, 1e-8)
        inner = (data["close"] - ts_min(data["low"], 12)) / divisor
        corr = correlation(rank(inner), rank(data["volume"]), 6)
        corr = corr.replace([-np.inf, np.inf], np.nan)
        return -1 * corr
