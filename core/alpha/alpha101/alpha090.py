"""Real WorldQuant Alpha101 formula — Alpha090: Price dispersion: ts_std(close, 10) / ts_mean(close, 10)"""
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
class Alpha090(AlphaFactor):
    """Alpha090: Price dispersion: ts_std(close, 10) / ts_mean(close, 10)"""

    @property
    def name(self) -> str:
        return "alpha090"

    @property
    def category(self) -> str:
        return "price_dispersion"

    @property
    def description(self) -> str:
        return "Alpha090: Price dispersion: ts_std(close, 10) / ts_mean(close, 10)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        c = data["close"]
        return ts_std(c, 10) / (ts_mean(c, 10) + 1e-8)
