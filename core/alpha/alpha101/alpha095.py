"""Real WorldQuant Alpha101 formula — Alpha095: (rank(open - ts_min(open, 12)) < ts_rank((rank(correlation(sma((high + low) / 2, 19), sma(adv40, 19), 13))^5), 12))"""
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
class Alpha095(AlphaFactor):
    """Alpha095: (rank(open - ts_min(open, 12)) < ts_rank((rank(correlation(sma((high + low) / 2, 19), sma(adv40, 19), 13))^5), 12))"""

    @property
    def name(self) -> str:
        return "alpha095"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha095: (rank(open - ts_min(open, 12)) < ts_rank((rank(correlation(sma((high + low) / 2, 19), sma(adv40, 19), 13))^5), 12))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv40 = data["volume"].rolling(40).mean()
        hl2 = (data["high"] + data["low"]) / 2
        corr = correlation(hl2.rolling(19).mean(), adv40.rolling(19).mean(), 13)
        r5 = rank(corr) ** 5
        right = ts_rank(r5, 12)
        cond = rank(data["open"] - ts_min(data["open"], 12)) < right
        return bool_to_float(cond, right, corr)
