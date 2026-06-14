"""Real WorldQuant Alpha101 formula — Alpha004: (-1 * Ts_Rank(rank(low), 9))"""
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
class Alpha004(AlphaFactor):
    """Alpha004: (-1 * Ts_Rank(rank(low), 9))"""

    @property
    def name(self) -> str:
        return "alpha004"

    @property
    def category(self) -> str:
        return "price_position"

    @property
    def description(self) -> str:
        return "Alpha004: (-1 * Ts_Rank(rank(low), 9))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return -1 * ts_rank(rank(data["low"]), 9)
