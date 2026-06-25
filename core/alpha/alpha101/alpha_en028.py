"""Real WorldQuant Alpha101 formula — alpha028"""
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
class Alpha028_en(AlphaFactor):
    """alpha028: scale(((correlation(adv20,low,5)+((high+low)/2))-close))"""

    @property
    def name(self) -> str:
        return "alpha_en_028"

    @property
    def category(self) -> str:
        return "price_position"

    @property
    def description(self) -> str:
        return "scale(((correlation(adv20,low,5)+((high+low)/2))-close))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv20 = ts_mean(data["volume"], 20)
        corr = correlation(adv20, data["low"], 5)
        mid_price = (data["high"] + data["low"]) / 2
        inner = corr + mid_price - data["close"]
        return scale(inner)
