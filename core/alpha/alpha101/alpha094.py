"""Real WorldQuant Alpha101 formula — Alpha094: (-1 * rank(vwap - ts_min(vwap, 12)) ^ ts_rank(correlation(ts_rank(vwap, 20), ts_rank(adv60, 4), 18), 3))"""
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
class Alpha094(AlphaFactor):
    """Alpha094: (-1 * rank(vwap - ts_min(vwap, 12)) ^ ts_rank(correlation(ts_rank(vwap, 20), ts_rank(adv60, 4), 18), 3))"""

    @property
    def name(self) -> str:
        return "alpha094"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha094: (-1 * rank(vwap - ts_min(vwap, 12)) ^ ts_rank(correlation(ts_rank(vwap, 20), ts_rank(adv60, 4), 18), 3))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        adv60 = data["volume"].rolling(60).mean()
        corr = correlation(ts_rank(vwap, 20), ts_rank(adv60, 4), 18)
        exp = ts_rank(corr, 3)
        base = rank(vwap - ts_min(vwap, 12))
        return -1 * (base ** exp)
