"""Real WorldQuant Alpha101 formula — Alpha078: (rank(correlation(ts_sum(((low * 0.352233) + (vwap * (1 - 0.352233))), 20), ts_sum(adv40, 20), 7)) ^ rank(correlation(rank(vwap), rank(volume), 6)))"""
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
class Alpha078(AlphaFactor):
    """Alpha078: (rank(correlation(ts_sum(((low * 0.352233) + (vwap * (1 - 0.352233))), 20), ts_sum(adv40, 20), 7)) ^ rank(correlation(rank(vwap), rank(volume), 6)))"""

    @property
    def name(self) -> str:
        return "alpha078"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha078: (rank(correlation(ts_sum(((low * 0.352233) + (vwap * (1 - 0.352233))), 20), ts_sum(adv40, 20), 7)) ^ rank(correlation(rank(vwap), rank(volume), 6)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        adv40 = data["volume"].rolling(40).mean()
        blended = data["low"] * 0.352233 + vwap * 0.647767
        corr1 = correlation(ts_sum(blended, 20), ts_sum(adv40, 20), 7)
        corr2 = correlation(rank(vwap), rank(data["volume"]), 6)
        return rank(corr1) ** rank(corr2)
