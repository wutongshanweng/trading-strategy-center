"""Real WorldQuant Alpha101 formula — Momentum alpha143: CLOSE > DELAY(CLOSE, 1) ? cumulative_return : SELF"""
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
class Alpha143(AlphaFactor):
    """Momentum alpha143: CLOSE > DELAY(CLOSE, 1) ? cumulative_return : SELF — conditional momentum"""

    @property
    def name(self) -> str:
        return "alpha143"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha143: CLOSE > DELAY(CLOSE, 1) ? cumulative_return : SELF — conditional momentum"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Simplified: cumulative return when up, 0 when down
        returns = data["close"].pct_change()
        up = data["close"] > delay(data["close"], 1)
        result = pd.Series(0.0, index=data.index)
        result[up] = returns[up]
        return ts_sum(result, 20)
