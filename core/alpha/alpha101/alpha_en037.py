"""Real WorldQuant Alpha101 formula — alpha037"""
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
class Alpha037_en(AlphaFactor):
    """alpha037: rank(correlation(delay((open-close),1),close,200))+rank((open-close))"""

    @property
    def name(self) -> str:
        return "alpha_en_037"

    @property
    def category(self) -> str:
        return "correlation"

    @property
    def description(self) -> str:
        return "rank(correlation(delay((open-close),1),close,200))+rank((open-close))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        delayed_diff = delay(data["close"] - data["open"], 1)
        corr = correlation(delayed_diff, data["close"], 200)
        rank1 = rank(corr)
        rank2 = rank(data["open"] - data["close"])
        return rank1 + rank2
