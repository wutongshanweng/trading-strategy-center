"""Real WorldQuant Alpha101 formula — Alpha044: (-1 * correlation(high, rank(volume), 5))"""
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
class Alpha044(AlphaFactor):
    """Alpha044: (-1 * correlation(high, rank(volume), 5))"""

    @property
    def name(self) -> str:
        return "alpha044"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha044: (-1 * correlation(high, rank(volume), 5))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        corr = correlation(data["high"], rank(data["volume"]), 5)
        corr = corr.replace([-np.inf, np.inf], np.nan)
        return -1 * corr
