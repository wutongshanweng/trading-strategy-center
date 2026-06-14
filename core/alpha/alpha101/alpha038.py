"""Real WorldQuant Alpha101 formula — Alpha038: (-1 * rank(Ts_Rank(close, 10))) * rank((close / open))"""
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
class Alpha038(AlphaFactor):
    """Alpha038: (-1 * rank(Ts_Rank(close, 10))) * rank((close / open))"""

    @property
    def name(self) -> str:
        return "alpha038"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha038: (-1 * rank(Ts_Rank(close, 10))) * rank((close / open))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        inner = data["close"] / data["open"]
        inner = inner.replace([-np.inf, np.inf], 1).fillna(1)
        return -1 * rank(ts_rank(data["close"], 10)) * rank(inner)
