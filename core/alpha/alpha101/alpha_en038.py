"""Real WorldQuant Alpha101 formula — alpha038"""
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
class Alpha038_en(AlphaFactor):
    """alpha038: ((-1*rank(ts_rank(close,10)))*rank((close/open)))"""

    @property
    def name(self) -> str:
        return "alpha_en_038"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "((-1*rank(ts_rank(close,10)))*rank((close/open)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        ts_rank_close = ts_rank(data["close"], 10)
        rank1 = -1 * rank(ts_rank_close)
        rank2 = rank(data["close"] / data["open"])
        return rank1 * rank2
