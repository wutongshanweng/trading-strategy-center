"""Real WorldQuant Alpha101 formula — Momentum alpha173: 3 * SMA(close, 13, 2) - 2 * SMA(SMA(close, 13, 2), 13, 2) + SMA(SMA(SMA(LOG(close), 13, 2), 13, 2), 13, 2)"""
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
class Alpha173(AlphaFactor):
    """Momentum alpha173: 3 * SMA(close, 13, 2) - 2 * SMA(SMA(close, 13, 2), 13, 2) + SMA(SMA(SMA(LOG(close), 13, 2), 13, 2), 13, 2)"""

    @property
    def name(self) -> str:
        return "alpha173"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha173: 3 * SMA(close, 13, 2) - 2 * SMA(SMA(close, 13, 2), 13, 2) + SMA(SMA(SMA(LOG(close), 13, 2), 13, 2), 13, 2)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Triple EMA components
        alpha = 2 / 14

        # First component
        ema1 = data["close"].ewm(alpha=alpha, adjust=False).mean()

        # Second component (EMA of EMA)
        ema2 = ema1.ewm(alpha=alpha, adjust=False).mean()

        # Third component (EMA of EMA of EMA of log)
        log_close = np.log(data["close"].clip(lower=1e-8))
        ema_log = log_close.ewm(alpha=alpha, adjust=False).mean()
        ema_ema_log = ema_log.ewm(alpha=alpha, adjust=False).mean()
        ema3 = ema_ema_log.ewm(alpha=alpha, adjust=False).mean()

        return 3 * ema1 - 2 * ema2 + ema3
