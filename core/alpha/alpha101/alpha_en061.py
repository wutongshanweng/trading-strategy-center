"""Real WorldQuant Alpha101 formula — alpha061"""
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
class Alpha061_en(AlphaFactor):
    """alpha061: rank((vwap-ts_min(vwap,16.12)))<rank(correlation(vwap,adv180,17.9))"""

    @property
    def name(self) -> str:
        return "alpha_en_061"

    @property
    def category(self) -> str:
        return "comparison"

    @property
    def description(self) -> str:
        return "rank((vwap-ts_min(vwap,16.12)))<rank(correlation(vwap,adv180,17.9))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv180 = ts_mean(data["volume"], 180)
        vwap_min = data["vwap"] - ts_min(data["vwap"], 16)
        rank1 = rank(vwap_min)
        corr = correlation(data["vwap"], adv180, 18)
        rank2 = rank(corr)
        return (rank1 < rank2).astype(float)
