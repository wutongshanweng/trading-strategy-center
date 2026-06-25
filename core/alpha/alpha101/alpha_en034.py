"""Real WorldQuant Alpha101 formula — alpha034"""
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
class Alpha034_en(AlphaFactor):
    """alpha034: rank((1-rank((stddev(returns,2)/stddev(returns,5))))+rank((-1*delta(close,1))))"""

    @property
    def name(self) -> str:
        return "alpha_en_034"

    @property
    def category(self) -> str:
        return "volatility"

    @property
    def description(self) -> str:
        return "rank((1-rank((stddev(returns,2)/stddev(returns,5))))+rank((-1*delta(close,1))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        returns = data["close"].pct_change()
        stddev_2 = ts_std(returns, 2)
        stddev_5 = ts_std(returns, 5)
        ratio = stddev_2 / (stddev_5 + 1e-9)
        rank1 = 1 - rank(ratio)
        rank2 = rank(-1 * delta(data["close"], 1))
        return rank(rank1 + rank2)
