"""Real WorldQuant Alpha101 formula — Alpha088: min(rank(decay_linear(((rank(open) + rank(low)) - (rank(high) + rank(close))), 8)), ts_rank(decay_linear(correlation(ts_rank(close, 8), ts_rank(adv60, 21), 8), 7), 3))"""
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
class Alpha088(AlphaFactor):
    """Alpha088: min(rank(decay_linear(((rank(open) + rank(low)) - (rank(high) + rank(close))), 8)), ts_rank(decay_linear(correlation(ts_rank(close, 8), ts_rank(adv60, 21), 8), 7), 3))"""

    @property
    def name(self) -> str:
        return "alpha088"

    @property
    def category(self) -> str:
        return "complex_signal"

    @property
    def description(self) -> str:
        return "Alpha088: min(rank(decay_linear(((rank(open) + rank(low)) - (rank(high) + rank(close))), 8)), ts_rank(decay_linear(correlation(ts_rank(close, 8), ts_rank(adv60, 21), 8), 7), 3))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv60 = data["volume"].rolling(60).mean()
        inner1 = (rank(data["open"]) + rank(data["low"])) - (rank(data["high"]) + rank(data["close"]))
        dl1 = decay_linear(inner1.to_frame(), 8).iloc[:, 0]
        t1 = rank(dl1)
        corr = correlation(ts_rank(data["close"], 8), ts_rank(adv60, 21), 8)
        dl2 = decay_linear(corr.to_frame(), 7).iloc[:, 0]
        t2 = ts_rank(dl2, 3)
        result = pd.concat([t1, t2], axis=1).min(axis=1)
        result[corr.isna()] = np.nan
        return result
