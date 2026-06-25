"""Real WorldQuant Alpha101 formula — alpha031"""
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
class Alpha031_en(AlphaFactor):
    """alpha031: (rank(rank(rank(decay_linear((-1*rank(rank(delta(close,10)))),10))))+rank((-1*delta(close,3))))+sign(scale(correlation(adv20,low,12)))"""

    @property
    def name(self) -> str:
        return "alpha_en_031"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "(rank(rank(rank(decay_linear((-1*rank(rank(delta(close,10)))),10))))+rank((-1*delta(close,3))))+sign(scale(correlation(adv20,low,12)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv20 = ts_mean(data["volume"], 20)
        delta_close_10 = delta(data["close"], 10)
        inner1 = -1 * rank(rank(delta_close_10))
        decay1 = decay_linear(inner1, 10)
        rank1 = rank(rank(rank(decay1)))
        rank2 = rank(-1 * delta(data["close"], 3))
        corr = correlation(adv20, data["low"], 12)
        sign_scale = np.sign(scale(corr))
        return rank1 + rank2 + sign_scale
