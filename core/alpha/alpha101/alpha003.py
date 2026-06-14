"""Real WorldQuant Alpha101 formula — Alpha003: (-1 * correlation(rank(open), rank(volume), 10))"""
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
class Alpha003(AlphaFactor):
    """Alpha003: (-1 * correlation(rank(open), rank(volume), 10))"""

    @property
    def name(self) -> str:
        return "alpha003"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha003: (-1 * correlation(rank(open), rank(volume), 10))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return -1 * correlation(rank(data["open"]), rank(data["volume"]), 10)
