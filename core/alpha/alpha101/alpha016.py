"""Real WorldQuant Alpha101 formula — Alpha016: (-1 * correlation(rank(high), rank(volume), 3))"""
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
class Alpha016(AlphaFactor):
    """Alpha016: (-1 * correlation(rank(high), rank(volume), 3))"""

    @property
    def name(self) -> str:
        return "alpha016"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha016: (-1 * correlation(rank(high), rank(volume), 3))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return -1 * correlation(rank(data["high"]), rank(data["volume"]), 3)
