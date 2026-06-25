"""Real WorldQuant Alpha101 formula — alpha029"""
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
class Alpha029_en(AlphaFactor):
    """alpha029: min(product(rank(rank(scale(log(sum(ts_min(rank(rank((-1*rank(delta((close-1),5))))),2),1))))),1),5)+ts_rank(delay((-1*returns),6),5)"""

    @property
    def name(self) -> str:
        return "alpha_en_029"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "min(product(rank(rank(scale(log(sum(ts_min(rank(rank((-1*rank(delta((close-1),5))))),2),1))))),1),5)+ts_rank(delay((-1*returns),6),5)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        returns = data["close"].pct_change()
        delta_close = delta(data["close"] - 1, 5)
        neg_rank = -1 * rank(delta_close)
        inner1 = ts_min(rank(rank(neg_rank)), 2)
        inner2 = ts_sum(inner1, 1)
        inner3 = np.log(inner2 + 1e-9)
        inner4 = scale(inner3)
        inner5 = rank(rank(inner4))
        product_val = ts_product(inner5, 1)
        min_val = ts_min(product_val, 5)
        ts_rank_part = ts_rank(delay(-1 * returns, 6), 5)
        return min_val + ts_rank_part
