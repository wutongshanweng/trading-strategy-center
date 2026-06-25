"""Real WorldQuant Alpha101 formula — Momentum alpha190: log((count(returns > daily_return, 20) - 1) * sum((returns - daily_return) ** 2, ...) / ...) — simplified skewness-like measure"""
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
class Alpha190(AlphaFactor):
    """Momentum alpha190: log((count(returns > daily_return, 20) - 1) * sum((returns - daily_return) ** 2, ...) / ...) — simplified skewness-like measure"""

    @property
    def name(self) -> str:
        return "alpha190"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha190: log((count(returns > daily_return, 20) - 1) * sum((returns - daily_return) ** 2, ...) / ...) — simplified skewness-like measure"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        returns = data["close"].pct_change()
        # Use rolling mean as proxy for daily_return
        daily_return = ts_mean(returns, 1)
        # Count of positive returns in window
        count_pos = returns.rolling(20).apply(lambda x: (x > daily_return.iloc[x.index[-1]]).sum(), raw=False)
        diff = returns - daily_return
        sum_sq = ts_sum(diff ** 2, 20)
        result = np.log((count_pos - 1) * sum_sq / 20 + 1e-8)
        return result
