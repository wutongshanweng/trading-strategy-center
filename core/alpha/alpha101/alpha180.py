"""Real WorldQuant Alpha101 formula — Momentum alpha180: (mean(volume, 20) < volume) ? ((-1 * ts_rank(abs(delta(close, 7)), 60)) * sign(delta(close, 7))) : (-1 * volume)"""
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
class Alpha180(AlphaFactor):
    """Momentum alpha180: (mean(volume, 20) < volume) ? ((-1 * ts_rank(abs(delta(close, 7)), 60)) * sign(delta(close, 7))) : (-1 * volume)"""

    @property
    def name(self) -> str:
        return "alpha180"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha180: (mean(volume, 20) < volume) ? ((-1 * ts_rank(abs(delta(close, 7)), 60)) * sign(delta(close, 7))) : (-1 * volume)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        mean_vol = ts_mean(data["volume"], 20)
        high_vol = mean_vol < data["volume"]

        delta_close = delta(data["close"], 7)
        ts_rank_abs = ts_rank(np.abs(delta_close), 60)
        sign_delta = np.sign(delta_close)

        result = pd.Series(-data["volume"], index=data.index)
        result[high_vol] = -ts_rank_abs[high_vol] * sign_delta[high_vol]
        return result
