"""Real WorldQuant Alpha101 formula — alpha057"""
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
class Alpha057_en(AlphaFactor):
    """alpha057: 0-(1*((close-vwap)/decay_linear(rank(ts_argmax(close,30)),2)))"""

    @property
    def name(self) -> str:
        return "alpha_en_057"

    @property
    def category(self) -> str:
        return "mean_reversion"

    @property
    def description(self) -> str:
        return "0-(1*((close-vwap)/decay_linear(rank(ts_argmax(close,30)),2)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        argmax_close = ts_argmax(data["close"], 30)
        rank_argmax = rank(argmax_close)
        decay_val = decay_linear(rank_argmax, 2)
        return -1 * (data["close"] - data["vwap"]) / (decay_val + 1e-9)
