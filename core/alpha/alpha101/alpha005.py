"""Real WorldQuant Alpha101 formula — Alpha005: (rank((open - (sum(vwap, 10) / 10))) * (-1 * abs(rank((close - vwap)))))"""
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
class Alpha005(AlphaFactor):
    """Alpha005: (rank((open - (sum(vwap, 10) / 10))) * (-1 * abs(rank((close - vwap)))))"""

    @property
    def name(self) -> str:
        return "alpha005"

    @property
    def category(self) -> str:
        return "vwap"

    @property
    def description(self) -> str:
        return "Alpha005: (rank((open - (sum(vwap, 10) / 10))) * (-1 * abs(rank((close - vwap)))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        term1 = rank(data["open"] - vwap)
        term2 = -1 * abs(rank(data["close"] - vwap))
        return term1 * term2
