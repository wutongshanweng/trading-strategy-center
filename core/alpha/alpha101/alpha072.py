"""Real WorldQuant Alpha101 formula — Alpha072: (rank(decay_linear(correlation(((high + low) / 2), adv40, 9), 10)) / rank(decay_linear(correlation(ts_rank(vwap, 4), ts_rank(volume, 19), 7), 3)))"""
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
class Alpha072(AlphaFactor):
    """Alpha072: (rank(decay_linear(correlation(((high + low) / 2), adv40, 9), 10)) / rank(decay_linear(correlation(ts_rank(vwap, 4), ts_rank(volume, 19), 7), 3)))"""

    @property
    def name(self) -> str:
        return "alpha072"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha072: (rank(decay_linear(correlation(((high + low) / 2), adv40, 9), 10)) / rank(decay_linear(correlation(ts_rank(vwap, 4), ts_rank(volume, 19), 7), 3)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        adv40 = data["volume"].rolling(40).mean()
        hl2 = (data["high"] + data["low"]) / 2
        corr1 = correlation(hl2, adv40, 9)
        dl1 = decay_linear(corr1.to_frame(), 10).iloc[:, 0]
        corr2 = correlation(ts_rank(vwap, 4), ts_rank(data["volume"], 19), 7)
        dl2 = decay_linear(corr2.to_frame(), 3).iloc[:, 0]
        return rank(dl1) / rank(dl2)
