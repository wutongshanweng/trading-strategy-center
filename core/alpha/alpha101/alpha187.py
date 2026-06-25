"""Real WorldQuant Alpha101 formula — Momentum alpha187: SUM((open <= delay(open, 1)) ? 0 : MAX((high - open), (open - delay(open, 1))), 20)"""
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
class Alpha187(AlphaFactor):
    """Momentum alpha187: SUM((open <= delay(open, 1)) ? 0 : MAX((high - open), (open - delay(open, 1))), 20)"""

    @property
    def name(self) -> str:
        return "alpha187"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha187: SUM((open <= delay(open, 1)) ? 0 : MAX((high - open), (open - delay(open, 1))), 20)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        d_open = delay(data["open"], 1)
        cond = data["open"] <= d_open
        term = np.maximum(data["high"] - data["open"], data["open"] - d_open)
        result = np.where(cond, 0, term)
        return ts_sum(pd.Series(result, index=data.index), 20)
