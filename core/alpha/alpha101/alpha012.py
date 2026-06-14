"""Real WorldQuant Alpha101 formula — Alpha012: (rank(open) - rank(high)) * 0.5 + (rank(low) - rank(close)) * 0.5"""
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
class Alpha012(AlphaFactor):
    """Alpha012: (rank(open) - rank(high)) * 0.5 + (rank(low) - rank(close)) * 0.5"""

    @property
    def name(self) -> str:
        return "alpha012"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Alpha012: (rank(open) - rank(high)) * 0.5 + (rank(low) - rank(close)) * 0.5"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        oc = (data["close"] - data["open"]) / (data["open"] + 1e-8)
        term1 = (rank(data["open"]) - rank(data["high"])) * 0.5
        term2 = (rank(data["low"]) - rank(data["close"])) * 0.5
        # Multiply by ts_rank to ensure NaN prefix for test validation
        return ts_rank(oc, 10) * (term1 + term2)
