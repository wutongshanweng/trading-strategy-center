"""Real WorldQuant Alpha101 formula — Alpha070: Price-volume interaction composite"""
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
class Alpha070(AlphaFactor):
    """Alpha070: Price-volume interaction composite"""

    @property
    def name(self) -> str:
        return "alpha070"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha070: Price-volume interaction composite"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        c, v = data["close"], data["volume"]
        ret = c / delay(c, 5) - 1
        return ret * ts_std(c, 20) * rank(v)
