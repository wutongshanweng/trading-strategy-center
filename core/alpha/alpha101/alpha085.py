"""Real WorldQuant Alpha101 formula — Alpha085: (rank(correlation((high * 0.876703) + (close * (1 - 0.876703)), adv30, 10)) ^ rank(correlation(ts_rank((high + low) / 2, 4), ts_rank(volume, 10), 7)))"""
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
class Alpha085(AlphaFactor):
    """Alpha085: (rank(correlation((high * 0.876703) + (close * (1 - 0.876703)), adv30, 10)) ^ rank(correlation(ts_rank((high + low) / 2, 4), ts_rank(volume, 10), 7)))"""

    @property
    def name(self) -> str:
        return "alpha085"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha085: (rank(correlation((high * 0.876703) + (close * (1 - 0.876703)), adv30, 10)) ^ rank(correlation(ts_rank((high + low) / 2, 4), ts_rank(volume, 10), 7)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv30 = data["volume"].rolling(30).mean()
        blended = data["high"] * 0.876703 + data["close"] * 0.123297
        corr1 = correlation(blended, adv30, 10)
        hl2 = (data["high"] + data["low"]) / 2
        corr2 = correlation(ts_rank(hl2, 4), ts_rank(data["volume"], 10), 7)
        return rank(corr1) ** rank(corr2)
