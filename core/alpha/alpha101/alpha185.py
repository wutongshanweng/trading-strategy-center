"""Real WorldQuant Alpha101 formula — Momentum alpha185: rank((-1 * ((1 - (open / close)) ** 2)))"""
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
class Alpha185(AlphaFactor):
    """Momentum alpha185: rank((-1 * ((1 - (open / close)) ** 2)))"""

    @property
    def name(self) -> str:
        return "alpha185"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha185: rank((-1 * ((1 - (open / close)) ** 2)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        ratio = 1 - (data["open"] / (data["close"] + 1e-8))
        inner = -1 * (ratio ** 2)
        return rank(inner)
