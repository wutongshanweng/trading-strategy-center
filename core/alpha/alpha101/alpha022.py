"""Real WorldQuant Alpha101 formula — Alpha022: (-1 * rank(delta(rank(close), 6)) * rank(delta(rank(volume), 6)))"""
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
class Alpha022(AlphaFactor):
    """Alpha022: (-1 * rank(delta(rank(close), 6)) * rank(delta(rank(volume), 6)))"""

    @property
    def name(self) -> str:
        return "alpha022"

    @property
    def category(self) -> str:
        return "price_volume"

    @property
    def description(self) -> str:
        return "Alpha022: (-1 * rank(delta(rank(close), 6)) * rank(delta(rank(volume), 6)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        dc = delta(rank(data["close"]), 6)
        dv = delta(rank(data["volume"]), 6)
        return -1 * rank(dc) * rank(dv)
