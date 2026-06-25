"""Real WorldQuant Alpha101 formula — alpha060"""
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
class Alpha060_en(AlphaFactor):
    """alpha060: 0-(1*((2*scale(rank(((((close-low)-(high-close))/(high-low))*volume))))-scale(rank(ts_argmax(close,10)))))"""

    @property
    def name(self) -> str:
        return "alpha_en_060"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "0-(1*((2*scale(rank(((((close-low)-(high-close))/(high-low))*volume))))-scale(rank(ts_argmax(close,10)))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        close_low = data["close"] - data["low"]
        high_close = data["high"] - data["close"]
        hl_range = data["high"] - data["low"] + 1e-9
        position = (close_low - high_close) / hl_range
        rank_pos = rank(position * data["volume"])
        scale1 = scale(rank_pos)
        argmax_rank = rank(ts_argmax(data["close"], 10))
        scale2 = scale(argmax_rank)
        return -1 * (2 * scale1 - scale2)
