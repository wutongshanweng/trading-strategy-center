"""Real WorldQuant Alpha101 formula — alpha066"""
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
class Alpha066_en(AlphaFactor):
    """alpha066: (rank(decay_linear(delta(vwap,3.5),7.2))+ts_rank(decay_linear(((((low*0.97)+(low*(1-0.97)))-vwap)/(open-((high+low)/2)),11.4),6.7))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_066"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "(rank(decay_linear(delta(vwap,3.5),7.2))+ts_rank(decay_linear(((((low*0.97)+(low*(1-0.97)))-vwap)/(open-((high+low)/2)),11.4),6.7))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        delta_vwap = delta(data["vwap"], 4)
        decay1 = decay_linear(delta_vwap, 7)
        rank1 = rank(decay1)
        mid = (data["high"] + data["low"]) / 2
        weighted_low = data["low"]
        ratio = (weighted_low - data["vwap"]) / (data["open"] - mid + 1e-9)
        decay2 = decay_linear(ratio, 11)
        ts_rank2 = ts_rank(decay2, 7)
        return (rank1 + ts_rank2) * -1
