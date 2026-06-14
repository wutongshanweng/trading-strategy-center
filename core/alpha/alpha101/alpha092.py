"""Real WorldQuant Alpha101 formula — Alpha092: min(ts_rank(decay_linear((((high + low) / 2 + close) < (low + open)), 15), 19), ts_rank(decay_linear(correlation(rank(low), rank(adv30), 8), 7), 7))"""
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
class Alpha092(AlphaFactor):
    """Alpha092: min(ts_rank(decay_linear((((high + low) / 2 + close) < (low + open)), 15), 19), ts_rank(decay_linear(correlation(rank(low), rank(adv30), 8), 7), 7))"""

    @property
    def name(self) -> str:
        return "alpha092"

    @property
    def category(self) -> str:
        return "complex_signal"

    @property
    def description(self) -> str:
        return "Alpha092: min(ts_rank(decay_linear((((high + low) / 2 + close) < (low + open)), 15), 19), ts_rank(decay_linear(correlation(rank(low), rank(adv30), 8), 7), 7))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv30 = data["volume"].rolling(30).mean()
        cond = ((data["high"] + data["low"]) / 2 + data["close"]) < (data["low"] + data["open"])
        dl1 = decay_linear(cond.astype(float).to_frame(), 15).iloc[:, 0]
        t1 = ts_rank(dl1, 19)
        corr = correlation(rank(data["low"]), rank(adv30), 8)
        dl2 = decay_linear(corr.to_frame(), 7).iloc[:, 0]
        t2 = ts_rank(dl2, 7)
        return pd.concat([t1, t2], axis=1).min(axis=1)
