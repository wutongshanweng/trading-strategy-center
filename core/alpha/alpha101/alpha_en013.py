"""Real WorldQuant Alpha101 formula — alpha013"""
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
class Alpha013_en(AlphaFactor):
    """alpha013: -1*rank(covariance(rank(close),rank(volume),5))"""

    @property
    def name(self) -> str:
        return "alpha_en_013"

    @property
    def category(self) -> str:
        return "correlation"

    @property
    def description(self) -> str:
        return "-1*rank(covariance(rank(close),rank(volume),5))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        rank_close = rank(data["close"])
        rank_vol = rank(data["volume"])
        cov = ts_cov(rank_close, rank_vol, 5)
        return -1 * rank(cov)
