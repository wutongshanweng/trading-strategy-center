"""Real WorldQuant Alpha101 formula — alpha093"""
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
class Alpha093_en(AlphaFactor):
    """alpha093: ts_rank(decay_linear(correlation(vwap,adv80,17.4),19.8),7.5)/rank(decay_linear(delta(((close*0.52)+(vwap*(1-0.52))),2.8),16.3))"""

    @property
    def name(self) -> str:
        return "alpha_en_093"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "ts_rank(decay_linear(correlation(vwap,adv80,17.4),19.8),7.5)/rank(decay_linear(delta(((close*0.52)+(vwap*(1-0.52))),2.8),16.3))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv80 = ts_mean(data["volume"], 80)
        corr = correlation(data["vwap"], adv80, 17)
        decay1 = decay_linear(corr, 20)
        ts_rank1 = ts_rank(decay1, 8)
        weighted = (data["close"] * 0.52) + (data["vwap"] * 0.48)
        delta_weighted = delta(weighted, 3)
        decay2 = decay_linear(delta_weighted, 16)
        rank2 = rank(decay2)
        return ts_rank1 / (rank2 + 1e-9)
