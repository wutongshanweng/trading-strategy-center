"""Real WorldQuant Alpha101 formula — Alpha007: ((adv20 < volume) ? ((-1 * ts_rank(abs(delta(close, 7)), 60)) * sign(delta(close, 7))) : (-1 * 1))"""
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
class Alpha007(AlphaFactor):
    """Alpha007: ((adv20 < volume) ? ((-1 * ts_rank(abs(delta(close, 7)), 60)) * sign(delta(close, 7))) : (-1 * 1))"""

    @property
    def name(self) -> str:
        return "alpha007"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha007: ((adv20 < volume) ? ((-1 * ts_rank(abs(delta(close, 7)), 60)) * sign(delta(close, 7))) : (-1 * 1))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv20 = data["volume"].rolling(20).mean()
        cond = adv20 < data["volume"]
        dc = delta(data["close"], 7)
        result = -1 * ts_rank(dc.abs(), 60) * np.sign(dc)
        return pd.Series(np.where(cond, result, -1.0), index=data.index)
