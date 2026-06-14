"""Real WorldQuant Alpha101 formula — Alpha021: (regression_slope(rank(close), 60) + correlation(rank(close), rank(volume), 10))"""
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
class Alpha021(AlphaFactor):
    """Alpha021: (regression_slope(rank(close), 60) + correlation(rank(close), rank(volume), 10))"""

    @property
    def name(self) -> str:
        return "alpha021"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha021: (regression_slope(rank(close), 60) + correlation(rank(close), rank(volume), 10))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        rc = rank(data["close"])
        slope = rc.rolling(60, min_periods=30).apply(lambda s: np.polyfit(range(len(s)), s, 1)[0] if len(s) > 0 else 0, raw=True)
        corr = correlation(rc, rank(data["volume"]), 10)
        return slope + corr
