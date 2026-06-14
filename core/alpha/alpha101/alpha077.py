"""Real WorldQuant Alpha101 formula — Alpha077: min(rank(decay_linear(((((high + low) / 2) + high) - (vwap + high)), 20)), rank(decay_linear(correlation((high + low) / 2, adv40, 3), 6)))"""
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
class Alpha077(AlphaFactor):
    """Alpha077: min(rank(decay_linear(((((high + low) / 2) + high) - (vwap + high)), 20)), rank(decay_linear(correlation((high + low) / 2, adv40, 3), 6)))"""

    @property
    def name(self) -> str:
        return "alpha077"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha077: min(rank(decay_linear(((((high + low) / 2) + high) - (vwap + high)), 20)), rank(decay_linear(correlation((high + low) / 2, adv40, 3), 6)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        adv40 = data["volume"].rolling(40).mean()
        hl2 = (data["high"] + data["low"]) / 2
        inner = (hl2 + data["high"]) - (vwap + data["high"])
        dl1 = decay_linear(inner.to_frame(), 20).iloc[:, 0]
        corr = correlation(hl2, adv40, 3)
        dl2 = decay_linear(corr.to_frame(), 6).iloc[:, 0]
        return pd.concat([rank(dl1), rank(dl2)], axis=1).min(axis=1)
