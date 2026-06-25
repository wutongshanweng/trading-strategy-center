"""Real WorldQuant Alpha101 formula — alpha020"""
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
class Alpha020_en(AlphaFactor):
    """alpha020: ((-1*rank((open-delay(high,1))))*rank((open-delay(close,1))))*rank((open-delay(low,1))))"""

    @property
    def name(self) -> str:
        return "alpha_en_020"

    @property
    def category(self) -> str:
        return "price_gap"

    @property
    def description(self) -> str:
        return "((-1*rank((open-delay(high,1))))*rank((open-delay(close,1))))*rank((open-delay(low,1))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        rank1 = -1 * rank(data["open"] - delay(data["high"], 1))
        rank2 = rank(data["open"] - delay(data["close"], 1))
        rank3 = rank(data["open"] - delay(data["low"], 1))
        return rank1 * rank2 * rank3
