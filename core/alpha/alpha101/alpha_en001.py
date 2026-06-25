"""Real WorldQuant Alpha101 formula — Momentum alpha001: (rank(Ts_ArgMax(...)))"""
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
class Alpha001_en(AlphaFactor):
    """Momentum alpha001: rank(ts_argmax(signedpower((returns<0?stddev(returns,20):close),2),5))-0.5"""

    @property
    def name(self) -> str:
        return "alpha_en_001"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "rank(ts_argmax(signedpower((returns<0?stddev(returns,20):close),2),5))-0.5"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        returns = data["close"].pct_change()
        cond = returns < 0
        inner = pd.Series(
            np.where(cond, returns.rolling(20).std(), data["close"]),
            index=data.index
        )
        sp = signedpower(inner, 2.0)
        arg = ts_argmax(sp, 5)
        return rank(arg) - 0.5
