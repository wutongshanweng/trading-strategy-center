"""Real WorldQuant Alpha101 formula — alpha077"""
import numpy as np
import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .operators import rank, ts_mean, correlation, decay_linear


@FactorRegistry.register
class Alpha077_en(AlphaFactor):
    """alpha077: min(rank(decay_linear(((((high+low)/2)+high)-(vwap+high)),20)),rank(decay_linear(correlation(((high+low)/2),adv40,3.2),5.6)))"""

    @property
    def name(self) -> str:
        return "alpha_en_077"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "min(rank(decay_linear(((((high+low)/2)+high)-(vwap+high)),20)),rank(decay_linear(correlation(((high+low)/2),adv40,3.2),5.6)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv40 = ts_mean(data["volume"], 40)
        mid = (data["high"] + data["low"]) / 2
        inner = (mid + data["high"]) - (data["vwap"] + data["high"])
        decay1 = decay_linear(inner, 20)
        rank1 = rank(decay1)
        corr = correlation(mid, adv40, 3)
        decay2 = decay_linear(corr, 6)
        rank2 = rank(decay2)
        return pd.concat([rank1, rank2], axis=1).min(axis=1)
