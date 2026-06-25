"""Real WorldQuant Alpha101 formula — alpha033"""
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
class Alpha033_en(AlphaFactor):
    """alpha033: rank((-1*((1-(open/close))^1)))"""

    @property
    def name(self) -> str:
        return "alpha_en_033"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "rank((-1*((1-(open/close))^1)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        ratio = 1 - (data["open"] / data["close"])
        inner = -1 * (ratio ** 1)
        return rank(inner)
