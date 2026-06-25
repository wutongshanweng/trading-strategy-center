"""Real WorldQuant Alpha101 formula — alpha075"""
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
class Alpha075_en(AlphaFactor):
    """alpha075: rank(correlation(vwap,volume,4.2))<rank(correlation(rank(low),rank(adv50),12.4))"""

    @property
    def name(self) -> str:
        return "alpha_en_075"

    @property
    def category(self) -> str:
        return "comparison"

    @property
    def description(self) -> str:
        return "rank(correlation(vwap,volume,4.2))<rank(correlation(rank(low),rank(adv50),12.4))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv50 = ts_mean(data["volume"], 50)
        corr1 = correlation(data["vwap"], data["volume"], 4)
        rank1 = rank(corr1)
        rank_low = rank(data["low"])
        rank_adv = rank(adv50)
        corr2 = correlation(rank_low, rank_adv, 12)
        rank2 = rank(corr2)
        return (rank1 < rank2).astype(float)
