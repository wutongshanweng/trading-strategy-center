"""Real WorldQuant Alpha101 formula — Momentum alpha184: rank(correlation(delay((open - close), 1), close, 200)) + rank((open - close))"""
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
class Alpha184(AlphaFactor):
    """Momentum alpha184: rank(correlation(delay((open - close), 1), close, 200)) + rank((open - close))"""

    @property
    def name(self) -> str:
        return "alpha184"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha184: rank(correlation(delay((open - close), 1), close, 200)) + rank((open - close))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        oc_diff = data["open"] - data["close"]
        delayed = delay(oc_diff, 1)
        corr = correlation(delayed, data["close"], 200)
        rank_corr = rank(corr)
        rank_oc = rank(oc_diff)
        return rank_corr + rank_oc
