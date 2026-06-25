"""Real WorldQuant Alpha101 formula — alpha098"""
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
class Alpha098_en(AlphaFactor):
    """alpha098: rank(decay_linear(correlation(vwap,sum(adv5,26.5),4.6),7.2))-rank(decay_linear(ts_rank(ts_argmin(correlation(rank(open),rank(adv15),20.8),8.6),7),8.1))"""

    @property
    def name(self) -> str:
        return "alpha_en_098"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "rank(decay_linear(correlation(vwap,sum(adv5,26.5),4.6),7.2))-rank(decay_linear(ts_rank(ts_argmin(correlation(rank(open),rank(adv15),20.8),8.6),7),8.1))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv5 = ts_mean(data["volume"], 5)
        adv15 = ts_mean(data["volume"], 15)
        sum_adv5 = ts_sum(adv5, 27)
        corr1 = correlation(data["vwap"], sum_adv5, 5)
        decay1 = decay_linear(corr1, 7)
        rank1 = rank(decay1)
        rank_open = rank(data["open"])
        rank_adv15 = rank(adv15)
        corr2 = correlation(rank_open, rank_adv15, 21)
        argmin_corr = ts_argmin(corr2, 9)
        ts_rank_val = ts_rank(argmin_corr, 7)
        decay2 = decay_linear(ts_rank_val, 8)
        rank2 = rank(decay2)
        return rank1 - rank2
