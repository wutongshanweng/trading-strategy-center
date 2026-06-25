"""Real WorldQuant Alpha101 formula — Momentum alpha146: mean(RET - SMA(RET, 61, 2), 20) * (RET - SMA(RET, 61, 2)) / SMA((RET - SMA(RET, 61, 2)) ** 2, 60)"""
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
class Alpha146(AlphaFactor):
    """Momentum alpha146: mean(RET - SMA(RET, 61, 2), 20) * (RET - SMA(RET, 61, 2)) / SMA((RET - SMA(RET, 61, 2)) ** 2, 60)"""

    @property
    def name(self) -> str:
        return "alpha146"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha146: mean(RET - SMA(RET, 61, 2), 20) * (RET - SMA(RET, 61, 2)) / SMA((RET - SMA(RET, 61, 2)) ** 2, 60)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        returns = data["close"].pct_change()
        sma_ret = returns.ewm(alpha=2/62, adjust=False).mean()
        diff = returns - sma_ret
        mean_diff = ts_mean(diff, 20)
        sq_diff = diff ** 2
        var = ts_mean(sq_diff, 60)
        return mean_diff * diff / (var + 1e-8)
