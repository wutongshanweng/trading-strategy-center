"""Real WorldQuant Alpha101 formula — Alpha099: (-1 * (rank(correlation(ts_sum((high + low) / 2, 20), ts_sum(adv60, 20), 9)) < rank(correlation(low, volume, 6))))"""
import numpy as np
import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .operators import (
    rank, ts_rank, ts_argmax, ts_argmin, ts_sum, ts_product,
    ts_min, ts_max, ts_mean, ts_std, ts_cov, correlation, covariance,
    scale, delay, delta, signedpower, decay_linear, signed_sqrt, bool_to_float,
)


@FactorRegistry.register
class Alpha099(AlphaFactor):
    """Alpha099: (-1 * (rank(correlation(ts_sum((high + low) / 2, 20), ts_sum(adv60, 20), 9)) < rank(correlation(low, volume, 6))))"""

    @property
    def name(self) -> str:
        return "alpha099"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha099: (-1 * (rank(correlation(ts_sum((high + low) / 2, 20), ts_sum(adv60, 20), 9)) < rank(correlation(low, volume, 6))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv60 = data["volume"].rolling(60).mean()
        hl2 = (data["high"] + data["low"]) / 2
        corr1 = correlation(ts_sum(hl2, 20), ts_sum(adv60, 20), 9)
        corr2 = correlation(data["low"], data["volume"], 6)
        cond = rank(corr1) < rank(corr2)
        return bool_to_float(cond, corr1, corr2, sign=-1.0)
