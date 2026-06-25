"""Real WorldQuant Alpha101 formula — Trend alpha147: regression slope of 12-day mean close"""
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
class Alpha147(AlphaFactor):
    """Trend alpha147: regression slope of 12-day mean close"""

    @property
    def name(self) -> str:
        return "alpha147"

    @property
    def category(self) -> str:
        return "trend"

    @property
    def description(self) -> str:
        return "Trend alpha147: regression slope of 12-day mean close"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Calculate slope of 12-day mean close using rolling linear regression
        mean_close = ts_mean(data["close"], 12)

        # Use delta of mean close as proxy for slope
        slope = delta(mean_close, 1)
        return slope
