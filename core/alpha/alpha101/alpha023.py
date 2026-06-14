"""Real WorldQuant Alpha101 formula — Alpha023: ((sum(high, 20) / 20) < high) ? (-1 * delta(high, 2)) : 0"""
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
class Alpha023(AlphaFactor):
    """Alpha023: ((sum(high, 20) / 20) < high) ? (-1 * delta(high, 2)) : 0"""

    @property
    def name(self) -> str:
        return "alpha023"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha023: ((sum(high, 20) / 20) < high) ? (-1 * delta(high, 2)) : 0"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        cond = data["high"].rolling(20).mean() < data["high"]
        dh2 = -1 * delta(data["high"], 2)
        return pd.Series(np.where(cond, dh2, 0.0), index=data.index)
