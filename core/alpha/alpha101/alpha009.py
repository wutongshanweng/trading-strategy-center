"""Real WorldQuant Alpha101 formula — Alpha009: ((0 < ts_min(delta(close, 1), 5)) ? delta(close, 1) : ((ts_max(delta(close, 1), 5) < 0) ? delta(close, 1) : (-1 * delta(close, 1))))"""
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
class Alpha009(AlphaFactor):
    """Alpha009: ((0 < ts_min(delta(close, 1), 5)) ? delta(close, 1) : ((ts_max(delta(close, 1), 5) < 0) ? delta(close, 1) : (-1 * delta(close, 1))))"""

    @property
    def name(self) -> str:
        return "alpha009"

    @property
    def category(self) -> str:
        return "trend"

    @property
    def description(self) -> str:
        return "Alpha009: ((0 < ts_min(delta(close, 1), 5)) ? delta(close, 1) : ((ts_max(delta(close, 1), 5) < 0) ? delta(close, 1) : (-1 * delta(close, 1))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        dc = delta(data["close"], 1)
        cond1 = 0 < ts_min(dc, 5)
        cond2 = ts_max(dc, 5) < 0
        result = np.where(cond1, dc, np.where(cond2, dc, -dc))
        return pd.Series(result, index=data.index)
