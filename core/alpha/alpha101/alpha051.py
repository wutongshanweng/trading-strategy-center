"""Real WorldQuant Alpha101 formula — Alpha051: (((((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)) < (-1 * 0.05)) ? 1 : ((-1 * 1) * (close - delay(close, 1))))"""
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
class Alpha051(AlphaFactor):
    """Alpha051: Conditional reversal based on slope threshold"""

    @property
    def name(self) -> str:
        return "alpha051"

    @property
    def category(self) -> str:
        return "price_reversal"

    @property
    def description(self) -> str:
        return "Alpha051: Conditional reversal based on slope threshold"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        inner = (((delay(data["close"], 20) - delay(data["close"], 10)) / 10) - ((delay(data["close"], 10) - data["close"]) / 10))
        alpha = pd.Series(-1 * delta(data["close"], 1), index=data.index)
        alpha[inner < -0.05] = 1
        return alpha
