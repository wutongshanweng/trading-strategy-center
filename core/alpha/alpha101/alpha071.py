"""Real WorldQuant Alpha101 formula — Alpha071: max(ts_rank(decay_linear(correlation(ts_rank(close, 4), ts_rank(adv180, 12), 18), 4), 16), ts_rank(decay_linear(rank((low + open) - (vwap + vwap))^2, 16), 4))"""
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
class Alpha071(AlphaFactor):
    """Alpha071: max(ts_rank(decay_linear(correlation(ts_rank(close, 4), ts_rank(adv180, 12), 18), 4), 16), ts_rank(decay_linear(rank((low + open) - (vwap + vwap))^2, 16), 4))"""

    @property
    def name(self) -> str:
        return "alpha071"

    @property
    def category(self) -> str:
        return "complex_signal"

    @property
    def description(self) -> str:
        return "Alpha071: max(ts_rank(decay_linear(correlation(ts_rank(close, 4), ts_rank(adv180, 12), 18), 4), 16), ts_rank(decay_linear(rank((low + open) - (vwap + vwap))^2, 16), 4))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        adv180 = data["volume"].rolling(180).mean()
        corr = correlation(ts_rank(data["close"], 4), ts_rank(adv180, 12), 18)
        dl1 = decay_linear(corr.to_frame(), 4).iloc[:, 0]
        t1 = ts_rank(dl1, 16)
        r = rank((data["low"] + data["open"]) - (vwap + vwap)) ** 2
        dl2 = decay_linear(r.to_frame(), 16).iloc[:, 0]
        t2 = ts_rank(dl2, 4)
        return pd.concat([t1, t2], axis=1).max(axis=1)
