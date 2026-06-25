"""Real WorldQuant Alpha101 formula — alpha032"""
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
class Alpha032_en(AlphaFactor):
    """alpha032: scale(((sum(close,7)/7)-close))+(20*scale(correlation(vwap,delay(close,5),230))))"""

    @property
    def name(self) -> str:
        return "alpha_en_032"

    @property
    def category(self) -> str:
        return "mean_reversion"

    @property
    def description(self) -> str:
        return "scale(((sum(close,7)/7)-close))+(20*scale(correlation(vwap,delay(close,5),230))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        avg_close_7 = ts_sum(data["close"], 7) / 7
        part1 = scale(avg_close_7 - data["close"])
        delayed_close = delay(data["close"], 5)
        corr = correlation(data["vwap"], delayed_close, 230)
        part2 = 20 * scale(corr)
        return part1 + part2
