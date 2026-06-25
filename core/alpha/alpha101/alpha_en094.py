"""Real WorldQuant Alpha101 formula — alpha094"""
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
class Alpha094_en(AlphaFactor):
    """alpha094: (rank((vwap-ts_min(vwap,11.6)))^ts_rank(correlation(ts_rank(vwap,19.6),ts_rank(adv60,4),18.1),2.7))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_094"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "(rank((vwap-ts_min(vwap,11.6)))^ts_rank(correlation(ts_rank(vwap,19.6),ts_rank(adv60,4),18.1),2.7))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv60 = ts_mean(data["volume"], 60)
        vwap_min = data["vwap"] - ts_min(data["vwap"], 12)
        rank1 = rank(vwap_min)
        ts_rank_vwap = ts_rank(data["vwap"], 20)
        ts_rank_adv = ts_rank(adv60, 4)
        corr = correlation(ts_rank_vwap, ts_rank_adv, 18)
        ts_rank2 = ts_rank(corr, 3)
        return (rank1 ** ts_rank2) * -1
