"""Real WorldQuant Alpha101 formula — Alpha079: Return momentum composite"""
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
class Alpha079(AlphaFactor):
    """Alpha079: Return momentum composite"""

    @property
    def name(self) -> str:
        return "alpha079"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Alpha079: Return momentum composite"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        ret = data["close"].pct_change()
        return rank(delta(ret, 5)) * rank(data["volume"])
