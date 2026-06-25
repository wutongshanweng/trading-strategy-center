"""Real WorldQuant Alpha101 formula — alpha041"""
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
class Alpha041_en(AlphaFactor):
    """alpha041: (((high*low)**0.5)-vwap)"""

    @property
    def name(self) -> str:
        return "alpha_en_041"

    @property
    def category(self) -> str:
        return "price_position"

    @property
    def description(self) -> str:
        return "(((high*low)**0.5)-vwap)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        hl_product = data["high"] * data["low"]
        sqrt_val = np.sqrt(hl_product + 1e-9)
        return sqrt_val - data["vwap"]
