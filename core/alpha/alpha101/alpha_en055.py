"""Real WorldQuant Alpha101 formula — alpha055"""
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
class Alpha055_en(AlphaFactor):
    """alpha055: -1*correlation(rank(((close-ts_min(low,12))/(ts_max(high,12)-ts_min(low,12)))),rank(volume),6)"""

    @property
    def name(self) -> str:
        return "alpha_en_055"

    @property
    def category(self) -> str:
        return "correlation"

    @property
    def description(self) -> str:
        return "-1*correlation(rank(((close-ts_min(low,12))/(ts_max(high,12)-ts_min(low,12)))),rank(volume),6)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        ts_min_low = ts_min(data["low"], 12)
        ts_max_high = ts_max(data["high"], 12)
        price_position = (data["close"] - ts_min_low) / (ts_max_high - ts_min_low + 1e-9)
        rank_pp = rank(price_position)
        rank_vol = rank(data["volume"])
        corr = correlation(rank_pp, rank_vol, 6)
        return -1 * corr
