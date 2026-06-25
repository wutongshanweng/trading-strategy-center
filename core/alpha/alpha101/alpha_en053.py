"""Real WorldQuant Alpha101 formula — alpha053"""
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
class Alpha053_en(AlphaFactor):
    """alpha053: -1*delta((((close-low)-(high-close))/(close-low)),9)"""

    @property
    def name(self) -> str:
        return "alpha_en_053"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "-1*delta((((close-low)-(high-close))/(close-low)),9)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        close_low = data["close"] - data["low"]
        high_close = data["high"] - data["close"]
        inner = (close_low - high_close) / (close_low + 1e-9)
        return -1 * delta(inner, 9)
