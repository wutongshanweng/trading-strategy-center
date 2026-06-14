"""Real WorldQuant Alpha101 formula — Alpha024: (((sum(close, 100) / 100) > close) ? (sign(-1 * delta(close, 7))) : (-1 * rank(1 + sum(returns, 250))))"""
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
class Alpha024(AlphaFactor):
    """Alpha024: (((sum(close, 100) / 100) > close) ? (sign(-1 * delta(close, 7))) : (-1 * rank(1 + sum(returns, 250))))"""

    @property
    def name(self) -> str:
        return "alpha024"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha024: (((sum(close, 100) / 100) > close) ? (sign(-1 * delta(close, 7))) : (-1 * rank(1 + sum(returns, 250))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        cond = data["close"].rolling(100).mean() > data["close"]
        sc7 = np.sign(-1 * delta(data["close"], 7))
        ret = data["close"].pct_change()
        sr250 = ret.rolling(250).sum()
        result = np.where(cond, sc7, -1 * rank(1 + sr250))
        return pd.Series(result, index=data.index)
