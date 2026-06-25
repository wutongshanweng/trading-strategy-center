"""Real WorldQuant Alpha101 formula — alpha025"""
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
class Alpha025_en(AlphaFactor):
    """alpha025: rank((((-1*returns)*adv20)*vwap)*(high-close))"""

    @property
    def name(self) -> str:
        return "alpha_en_025"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "rank((((-1*returns)*adv20)*vwap)*(high-close))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        returns = data["close"].pct_change()
        adv20 = ts_mean(data["volume"], 20)
        inner = (-1 * returns) * adv20 * data["vwap"] * (data["high"] - data["close"])
        return rank(inner)
