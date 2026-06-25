"""Real WorldQuant Alpha101 formula — alpha069"""
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
class Alpha069_en(AlphaFactor):
    """alpha069: (rank(delta(vwap,2.7))^ts_rank(correlation(((close*0.49)+(vwap*(1-0.49))),adv20,4.9),9.1))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_069"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "(rank(delta(vwap,2.7))^ts_rank(correlation(((close*0.49)+(vwap*(1-0.49))),adv20,4.9),9.1))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv20 = ts_mean(data["volume"], 20)
        delta_vwap = delta(data["vwap"], 3)
        rank1 = rank(delta_vwap)
        weighted = (data["close"] * 0.49) + (data["vwap"] * 0.51)
        corr = correlation(weighted, adv20, 5)
        ts_rank2 = ts_rank(corr, 9)
        return (rank1 ** ts_rank2) * -1
