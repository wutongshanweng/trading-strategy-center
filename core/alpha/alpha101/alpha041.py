"""Real WorldQuant Alpha101 formula — Alpha041: (((high * low)^0.5) - vwap)"""
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
class Alpha041(AlphaFactor):
    """Alpha041: (((high * low)^0.5) - vwap)"""

    @property
    def name(self) -> str:
        return "alpha041"

    @property
    def category(self) -> str:
        return "price_structure"

    @property
    def description(self) -> str:
        return "Alpha041: (((high * low)^0.5) - vwap)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        return np.sqrt(data["high"] * data["low"]) - vwap
