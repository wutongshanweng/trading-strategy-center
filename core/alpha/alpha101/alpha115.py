"""Real WorldQuant Alpha101 formula — Momentum alpha115: rank(correlation((high * 0.9 + close * 0.1), mean(volume, 30), 10)) ** rank(correlation(ts_rank(((high + low) / 2), 4), ts_rank(volume, 10), 7))"""
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
class Alpha115(AlphaFactor):
    """Momentum alpha115: rank(correlation((high * 0.9 + close * 0.1), mean(volume, 30), 10)) ** rank(correlation(ts_rank(((high + low) / 2), 4), ts_rank(volume, 10), 7))"""

    @property
    def name(self) -> str:
        return "alpha115"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha115: rank(correlation((high * 0.9 + close * 0.1), mean(volume, 30), 10)) ** rank(correlation(ts_rank(((high + low) / 2), 4), ts_rank(volume, 10), 7))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        hl = (data["high"] + data["low"]) / 2
        hp = data["high"] * 0.9 + data["close"] * 0.1
        mean_vol_30 = ts_mean(data["volume"], 30)
        corr1 = correlation(hp, mean_vol_30, 10)
        rank_corr1 = rank(corr1)

        ts_rank_hl = ts_rank(hl, 4)
        ts_rank_vol = ts_rank(data["volume"], 10)
        corr2 = correlation(ts_rank_hl, ts_rank_vol, 7)
        rank_corr2 = rank(corr2)

        return rank_corr1 ** rank_corr2
