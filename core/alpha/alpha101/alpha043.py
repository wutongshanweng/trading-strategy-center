"""Real WorldQuant Alpha101 formula — Alpha043: (ts_rank((volume / adv20), 20) * ts_rank((-1 * delta(close, 7)), 8))"""
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
class Alpha043(AlphaFactor):
    """Alpha043: (ts_rank((volume / adv20), 20) * ts_rank((-1 * delta(close, 7)), 8))"""

    @property
    def name(self) -> str:
        return "alpha043"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha043: (ts_rank((volume / adv20), 20) * ts_rank((-1 * delta(close, 7)), 8))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv20 = data["volume"].rolling(20).mean()
        return ts_rank(data["volume"] / adv20, 20) * ts_rank(-1 * delta(data["close"], 7), 8)
