"""Real WorldQuant Alpha101 formula — alpha089"""
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
class Alpha089_en(AlphaFactor):
    """alpha089: ts_rank(decay_linear(correlation(((low*0.97)+(low*(1-0.97))),adv10,6.9),5.5),3.8)-ts_rank(decay_linear(delta(vwap,3.5),10.1),15.3)"""

    @property
    def name(self) -> str:
        return "alpha_en_089"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "ts_rank(decay_linear(correlation(((low*0.97)+(low*(1-0.97))),adv10,6.9),5.5),3.8)-ts_rank(decay_linear(delta(vwap,3.5),10.1),15.3)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv10 = ts_mean(data["volume"], 10)
        weighted_low = data["low"]
        corr = correlation(weighted_low, adv10, 7)
        decay1 = decay_linear(corr, 6)
        ts_rank1 = ts_rank(decay1, 4)
        delta_vwap = delta(data["vwap"], 4)
        decay2 = decay_linear(delta_vwap, 10)
        ts_rank2 = ts_rank(decay2, 15)
        return ts_rank1 - ts_rank2
