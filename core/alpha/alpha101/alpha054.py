"""Real WorldQuant Alpha101 formula — Alpha054: ((-1 * ((low - close) * (open^5))) / ((low - high) * (close^5)))"""
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
class Alpha054(AlphaFactor):
    """Alpha054: ((-1 * ((low - close) * (open^5))) / ((low - high) * (close^5)))"""

    @property
    def name(self) -> str:
        return "alpha054"

    @property
    def category(self) -> str:
        return "price_structure"

    @property
    def description(self) -> str:
        return "Alpha054: ((-1 * ((low - close) * (open^5))) / ((low - high) * (close^5)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        divisor = (data["low"] - data["high"]).replace(0, -1e-8)
        return -1 * (data["low"] - data["close"]) * (data["open"] ** 5) / (divisor * (data["close"] ** 5))
