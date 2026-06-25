"""Real WorldQuant Alpha101 formula — alpha063"""
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
class Alpha063_en(AlphaFactor):
    """alpha063: (rank(decay_linear(delta(close,2.25),8.2))-rank(decay_linear(correlation(((vwap*0.32)+(open*(1-0.32))),sum(adv180,37.2),13.6),12.3)))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_063"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "(rank(decay_linear(delta(close,2.25),8.2))-rank(decay_linear(correlation(((vwap*0.32)+(open*(1-0.32))),sum(adv180,37.2),13.6),12.3)))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv180 = ts_mean(data["volume"], 180)
        sum_adv = ts_sum(adv180, 37)
        delta_close = delta(data["close"], 2)
        decay1 = decay_linear(delta_close, 8)
        weighted = (data["vwap"] * 0.32) + (data["open"] * 0.68)
        corr = correlation(weighted, sum_adv, 14)
        decay2 = decay_linear(corr, 12)
        return (rank(decay1) - rank(decay2)) * -1
