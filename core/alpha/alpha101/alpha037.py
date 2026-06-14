"""Real WorldQuant Alpha101 formula — Alpha037: (rank(correlation(delay((open - close), 1), close, 200)) + rank((open - close)))"""
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
class Alpha037(AlphaFactor):
    """Alpha037: (rank(correlation(delay((open - close), 1), close, 200)) + rank((open - close)))"""

    @property
    def name(self) -> str:
        return "alpha037"

    @property
    def category(self) -> str:
        return "price_momentum"

    @property
    def description(self) -> str:
        return "Alpha037: (rank(correlation(delay((open - close), 1), close, 200)) + rank((open - close)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        w = min(200, len(data) - 1)
        corr = correlation(delay(data["open"] - data["close"], 1), data["close"], w)
        return rank(corr) + rank(data["open"] - data["close"])
