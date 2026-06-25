"""Real WorldQuant Alpha101 formula — alpha068"""
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
class Alpha068_en(AlphaFactor):
    """alpha068: (ts_rank(correlation(rank(high),rank(adv15),8.9),13.9)<rank(delta(((close*0.52)+(low*(1-0.52))),1.06)))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_068"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "(ts_rank(correlation(rank(high),rank(adv15),8.9),13.9)<rank(delta(((close*0.52)+(low*(1-0.52))),1.06)))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv15 = ts_mean(data["volume"], 15)
        rank_high = rank(data["high"])
        rank_adv = rank(adv15)
        corr = correlation(rank_high, rank_adv, 9)
        ts_rank1 = ts_rank(corr, 14)
        weighted = (data["close"] * 0.52) + (data["low"] * 0.48)
        delta_weighted = delta(weighted, 1)
        rank2 = rank(delta_weighted)
        cond = ts_rank1 < rank2
        return pd.Series(np.where(cond, -1.0, 0.0), index=data.index)
