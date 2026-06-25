"""Real WorldQuant Alpha101 formula — alpha011"""
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
class Alpha011_en(AlphaFactor):
    """alpha011: (rank(ts_max((vwap-close),3))+rank(ts_min((vwap-close),3)))*rank(delta(volume,3))"""

    @property
    def name(self) -> str:
        return "alpha_en_011"

    @property
    def category(self) -> str:
        return "price_volume"

    @property
    def description(self) -> str:
        return "(rank(ts_max((vwap-close),3))+rank(ts_min((vwap-close),3)))*rank(delta(volume,3))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap_diff = data["vwap"] - data["close"]
        rank_max = rank(ts_max(vwap_diff, 3))
        rank_min = rank(ts_min(vwap_diff, 3))
        rank_vol_delta = rank(delta(data["volume"], 3))
        return (rank_max + rank_min) * rank_vol_delta
