"""Real WorldQuant Alpha101 formula — Momentum alpha122: delta(SMA(log(close), 13, 2), 1)"""
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
class Alpha122(AlphaFactor):
    """Momentum alpha122: delta(SMA(log(close), 13, 2), 1) — log price triple EMA, then delta"""

    @property
    def name(self) -> str:
        return "alpha122"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha122: delta(SMA(log(close), 13, 2), 1) — log price triple EMA, then delta"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        log_close = np.log(data["close"].clip(lower=1e-8))
        sma = log_close.ewm(alpha=2/14, adjust=False).mean()
        return delta(sma, 1)
