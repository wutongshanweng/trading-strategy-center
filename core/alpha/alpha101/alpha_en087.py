"""Real WorldQuant Alpha101 formula — alpha087"""
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
class Alpha087_en(AlphaFactor):
    """alpha087: (max(rank(decay_linear(delta(((close*0.37)+(vwap*(1-0.37))),1.9),2.7)),ts_rank(decay_linear(abs(correlation(adv80,close,13.4)),4.9),14.5))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_087"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "(max(rank(decay_linear(delta(((close*0.37)+(vwap*(1-0.37))),1.9),2.7)),ts_rank(decay_linear(abs(correlation(adv80,close,13.4)),4.9),14.5))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv80 = ts_mean(data["volume"], 80)
        weighted = (data["close"] * 0.37) + (data["vwap"] * 0.63)
        delta_weighted = delta(weighted, 2)
        decay1 = decay_linear(delta_weighted, 3)
        rank1 = rank(decay1)
        corr = abs(correlation(adv80, data["close"], 13))
        decay2 = decay_linear(corr, 5)
        ts_rank2 = ts_rank(decay2, 15)
        combined = pd.concat([pd.Series(rank1.values), pd.Series(ts_rank2.values)], axis=1).max(axis=1)
        return combined * -1
