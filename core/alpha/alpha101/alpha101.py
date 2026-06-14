"""Real WorldQuant Alpha101 formula — Alpha101: ((close - open) / ((high - low) + 0.001))"""
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
class Alpha101(AlphaFactor):
    """Alpha101: ((close - open) / ((high - low) + 0.001))"""

    @property
    def name(self) -> str:
        return "alpha101"

    @property
    def category(self) -> str:
        return "price_structure"

    @property
    def description(self) -> str:
        return "Alpha101: ((close - open) / ((high - low) + 0.001))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return (data["close"] - data["open"]) / (data["high"] - data["low"] + 0.001)
