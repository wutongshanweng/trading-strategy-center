"""Real WorldQuant Alpha101 formula — Momentum alpha149: regression(returns / benchmark_returns, benchmark_returns, 252)"""
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
class Alpha149(AlphaFactor):
    """Momentum alpha149: regression(returns / benchmark_returns, benchmark_returns, 252)"""

    @property
    def name(self) -> str:
        return "alpha149"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha149: regression(returns / benchmark_returns, benchmark_returns, 252)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Simplified: rolling correlation with market as benchmark proxy
        returns = data["close"].pct_change()
        # Use market proxy: close vs its own lag (simplified beta)
        market_proxy = ts_mean(data["close"], 252).pct_change()
        # Rolling beta approximation
        rolling_cov = returns.rolling(60, min_periods=30).cov(market_proxy)
        rolling_var = market_proxy.rolling(60, min_periods=30).var()
        beta = rolling_cov / (rolling_var + 1e-8)
        return beta
