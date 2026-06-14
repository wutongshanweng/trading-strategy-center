"""Real WorldQuant Alpha101 formula — Alpha073: -1 * max(rank(decay_linear(delta(vwap, 5), 3)), ts_rank(decay_linear((delta((open * 0.147155) + (low * (1 - 0.147155)), 2) / ((open * 0.147155) + (low * (1 - 0.147155))) * -1), 3), 17))"""
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
class Alpha073(AlphaFactor):
    """Alpha073: Max of decay-linear vwap change vs ts_rank of blended open-low ratio"""

    @property
    def name(self) -> str:
        return "alpha073"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha073: Max of decay-linear vwap change vs ts_rank of blended open-low ratio"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        dl1 = decay_linear(delta(vwap, 5).to_frame(), 3).iloc[:, 0]
        blended = data["open"] * 0.147155 + data["low"] * 0.852845
        ratio = delta(blended, 2) / (blended + 1e-8) * -1
        dl2 = decay_linear(ratio.to_frame(), 3).iloc[:, 0]
        r2 = ts_rank(dl2, 17)
        t1 = rank(dl1)
        return -1 * pd.concat([t1, r2], axis=1).max(axis=1)
