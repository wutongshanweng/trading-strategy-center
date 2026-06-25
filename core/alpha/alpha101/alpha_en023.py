"""Real WorldQuant Alpha101 formula — alpha023"""
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
class Alpha023_en(AlphaFactor):
    """alpha023: (((sum(high,20)/20)<high)?(-1*delta(high,2)):0)"""

    @property
    def name(self) -> str:
        return "alpha_en_023"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "(((sum(high,20)/20)<high)?(-1*delta(high,2)):0)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        avg_high_20 = ts_sum(data["high"], 20) / 20
        cond = avg_high_20 < data["high"]
        delta_high_2 = delta(data["high"], 2)
        return pd.Series(np.where(cond, -1 * delta_high_2, 0.0), index=data.index)
