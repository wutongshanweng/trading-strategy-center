"""Real WorldQuant Alpha101 formula — alpha042"""
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
class Alpha042_en(AlphaFactor):
    """alpha042: rank((vwap-close))/(vwap+close)"""

    @property
    def name(self) -> str:
        return "alpha_en_042"

    @property
    def category(self) -> str:
        return "price_vwap"

    @property
    def description(self) -> str:
        return "rank((vwap-close))/(vwap+close)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        numerator = data["vwap"] - data["close"]
        denominator = data["vwap"] + data["close"]
        return rank(numerator) / (denominator + 1e-9)
