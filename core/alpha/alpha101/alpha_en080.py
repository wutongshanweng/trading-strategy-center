"""Real WorldQuant Alpha101 formula — alpha080"""
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
class Alpha080_en(AlphaFactor):
    """alpha080: ((rank(sign(delta(close,4)))^ts_rank(correlation(high,adv10,5.5),5.5))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_080"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "((rank(sign(delta(close,4)))^ts_rank(correlation(high,adv10,5.5),5.5))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv10 = ts_mean(data["volume"], 10)
        delta_close = delta(data["close"], 4)
        sign_val = np.sign(delta_close)
        rank1 = rank(sign_val)
        corr = correlation(data["high"], adv10, 6)
        ts_rank2 = ts_rank(corr, 6)
        return (rank1 ** ts_rank2) * -1
