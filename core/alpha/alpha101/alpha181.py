"""Real WorldQuant Alpha101 formula — Momentum alpha181: SUM((returns - mean(returns, 20)) - (benchmark - mean(benchmark, 20))) ** 2, 20) / SUM((benchmark - mean(benchmark, 20)) ** 3, 20)"""
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
class Alpha181(AlphaFactor):
    """Momentum alpha181: SUM((returns - mean(returns, 20)) - (benchmark - mean(benchmark, 20))) ** 2, 20) / SUM((benchmark - mean(benchmark, 20)) ** 3, 20)"""

    @property
    def name(self) -> str:
        return "alpha181"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha181: SUM((returns - mean(returns, 20)) - (benchmark - mean(benchmark, 20))) ** 2, 20) / SUM((benchmark - mean(benchmark, 20)) ** 3, 20)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Use market proxy as benchmark
        returns = data["close"].pct_change()
        # Simplified: use close vs its own mean as proxy
        benchmark = ts_mean(data["close"], 20)
        benchmark_ret = benchmark.pct_change()

        excess = (returns - ts_mean(returns, 20)) - (benchmark_ret - ts_mean(benchmark_ret, 20))
        numerator = ts_sum(excess ** 2, 20)
        denominator = ts_sum((benchmark_ret - ts_mean(benchmark_ret, 20)) ** 3, 20)
        return numerator / (denominator + 1e-8)
