"""Real WorldQuant Alpha101 formula — alpha083"""
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
class Alpha083_en(AlphaFactor):
    """alpha083: (rank(delay(((high-low)/(sum(close,5)/5)),2))*rank(rank(volume)))/(((high-low)/(sum(close,5)/5))/(vwap-close))"""

    @property
    def name(self) -> str:
        return "alpha_en_083"

    @property
    def category(self) -> str:
        return "volatility"

    @property
    def description(self) -> str:
        return "(rank(delay(((high-low)/(sum(close,5)/5)),2))*rank(rank(volume)))/(((high-low)/(sum(close,5)/5))/(vwap-close))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        hl_range = data["high"] - data["low"]
        avg_close_5 = ts_sum(data["close"], 5) / 5
        ratio = hl_range / (avg_close_5 + 1e-9)
        delayed = delay(ratio, 2)
        rank1 = rank(delayed)
        rank_vol = rank(rank(data["volume"]))
        numerator = rank1 * rank_vol
        denominator = ratio / (data["vwap"] - data["close"] + 1e-9)
        return numerator / (denominator + 1e-9)
