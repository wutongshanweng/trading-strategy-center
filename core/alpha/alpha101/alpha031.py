"""Real WorldQuant Alpha101 formula — Alpha031: (rank(rank(rank(decay_linear((-1 * rank(rank(delta(close, 10)))), 10)))) + rank((-1 * delta(close, 3))) + sign(scale(correlation(adv20, low, 12))))"""
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
class Alpha031(AlphaFactor):
    """Alpha031: (rank(rank(rank(decay_linear((-1 * rank(rank(delta(close, 10)))), 10)))) + rank((-1 * delta(close, 3))) + sign(scale(correlation(adv20, low, 12))))"""

    @property
    def name(self) -> str:
        return "alpha031"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha031: (rank(rank(rank(decay_linear((-1 * rank(rank(delta(close, 10)))), 10)))) + rank((-1 * delta(close, 3))) + sign(scale(correlation(adv20, low, 12))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv20 = data["volume"].rolling(20).mean()
        corr = correlation(adv20, data["low"], 12).replace([-np.inf, np.inf], 0).fillna(0)
        p1 = rank(rank(rank(decay_linear((-1 * rank(rank(delta(data["close"], 10)))).to_frame(), 10).iloc[:, 0])))
        p2 = rank((-1 * delta(data["close"], 3)))
        p3 = np.sign(scale(corr))
        return p1 + p2 + p3
