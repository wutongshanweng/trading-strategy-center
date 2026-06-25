"""Real WorldQuant Alpha101 formula — Momentum alpha166: -20 * (20 - 1) ** 1.5 * SUM(returns - mean(returns, 20), 20) / ((20 - 1) * (20 - 2) * std(returns, 20) ** 1.5)"""
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
class Alpha166(AlphaFactor):
    """Momentum alpha166: -20 * (20 - 1) ** 1.5 * SUM(returns - mean(returns, 20), 20) / ((20 - 1) * (20 - 2) * std(returns, 20) ** 1.5)"""

    @property
    def name(self) -> str:
        return "alpha166"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha166: -20 * (20 - 1) ** 1.5 * SUM(returns - mean(returns, 20), 20) / ((20 - 1) * (20 - 2) * std(returns, 20) ** 1.5)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        returns = data["close"].pct_change()
        mean_ret = ts_mean(returns, 20)
        diff = returns - mean_ret
        sum_diff = ts_sum(diff, 20)
        std_ret = ts_std(returns, 20)

        n = 20
        numerator = -20 * (n - 1) ** 1.5 * sum_diff
        denominator = (n - 1) * (n - 2) * (std_ret ** 1.5 + 1e-8)
        return numerator / denominator
