"""Real WorldQuant Alpha101 formula — alpha005"""
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
class Alpha005_en(AlphaFactor):
    """alpha005: rank(open-sum(vwap,10)/10)*(-1*abs(rank(close-vwap)))"""

    @property
    def name(self) -> str:
        return "alpha_en_005"

    @property
    def category(self) -> str:
        return "price_vwap"

    @property
    def description(self) -> str:
        return "rank(open-sum(vwap,10)/10)*(-1*abs(rank(close-vwap)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        sum_vwap_10 = ts_sum(data["vwap"], 10)
        avg_vwap = sum_vwap_10 / 10
        rank_open_part = rank(data["open"] - avg_vwap)
        rank_vwap_diff = rank(data["close"] - data["vwap"])
        return rank_open_part * (-1 * abs(rank_vwap_diff))
