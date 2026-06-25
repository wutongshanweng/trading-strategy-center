"""Real WorldQuant Alpha101 formula — alpha054"""
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
class Alpha054_en(AlphaFactor):
    """alpha054: (-1*((low-close)*(open**5)))/((low-high)*(close**5))"""

    @property
    def name(self) -> str:
        return "alpha_en_054"

    @property
    def category(self) -> str:
        return "price_position"

    @property
    def description(self) -> str:
        return "(-1*((low-close)*(open**5)))/((low-high)*(close**5))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        numerator = -1 * (data["low"] - data["close"]) * (data["open"] ** 5)
        denominator = (data["low"] - data["high"]) * (data["close"] ** 5)
        return numerator / (denominator + 1e-9)
