"""Real WorldQuant Alpha101 formula — Alpha034: rank(((1 - rank((stddev(returns, 2) / stddev(returns, 5)))) + (1 - rank(delta(close, 1)))))"""
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
class Alpha034(AlphaFactor):
    """Alpha034: rank(((1 - rank((stddev(returns, 2) / stddev(returns, 5)))) + (1 - rank(delta(close, 1)))))"""

    @property
    def name(self) -> str:
        return "alpha034"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Alpha034: rank(((1 - rank((stddev(returns, 2) / stddev(returns, 5)))) + (1 - rank(delta(close, 1)))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        ret = data["close"].pct_change()
        inner = ts_std(ret, 2) / (ts_std(ret, 5) + 1e-8)
        inner = inner.replace([-np.inf, np.inf], 1).fillna(1)
        return rank(2 - rank(inner) - rank(delta(data["close"], 1)))
