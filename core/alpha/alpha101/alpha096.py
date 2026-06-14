"""Real WorldQuant Alpha101 formula — Alpha096: (-1 * max(ts_rank(decay_linear(correlation(rank(vwap), rank(volume), 4), 4), 8), ts_rank(decay_linear(ts_argmax(correlation(ts_rank(close, 7), ts_rank(adv60, 4), 4), 13), 14), 13)))"""
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
class Alpha096(AlphaFactor):
    """Alpha096: (-1 * max(ts_rank(decay_linear(correlation(rank(vwap), rank(volume), 4), 4), 8), ts_rank(decay_linear(ts_argmax(correlation(ts_rank(close, 7), ts_rank(adv60, 4), 4), 13), 14), 13)))"""

    @property
    def name(self) -> str:
        return "alpha096"

    @property
    def category(self) -> str:
        return "complex_signal"

    @property
    def description(self) -> str:
        return "Alpha096: (-1 * max(ts_rank(decay_linear(correlation(rank(vwap), rank(volume), 4), 4), 8), ts_rank(decay_linear(ts_argmax(correlation(ts_rank(close, 7), ts_rank(adv60, 4), 4), 13), 14), 13)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        adv60 = data["volume"].rolling(60).mean()
        corr1 = correlation(rank(vwap), rank(data["volume"]), 4)
        dl1 = decay_linear(corr1.to_frame(), 4).iloc[:, 0]
        t1 = ts_rank(dl1, 8)
        corr2 = correlation(ts_rank(data["close"], 7), ts_rank(adv60, 4), 4)
        argmax = ts_argmax(corr2, 13)
        dl2 = decay_linear(argmax.to_frame(), 14).iloc[:, 0]
        t2 = ts_rank(dl2, 13)
        return -1 * pd.concat([t1, t2], axis=1).max(axis=1)
