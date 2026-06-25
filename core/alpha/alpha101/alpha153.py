"""Real WorldQuant Alpha101 formula — Momentum alpha153: (mean(close, 3) + mean(close, 6) + mean(close, 12) + mean(close, 24)) / 4"""
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
class Alpha153(AlphaFactor):
    """Momentum alpha153: (mean(close, 3) + mean(close, 6) + mean(close, 12) + mean(close, 24)) / 4 — Guppy multiple moving average"""

    @property
    def name(self) -> str:
        return "alpha153"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha153: (mean(close, 3) + mean(close, 6) + mean(close, 12) + mean(close, 24)) / 4 — Guppy multiple moving average"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        mean_3 = ts_mean(data["close"], 3)
        mean_6 = ts_mean(data["close"], 6)
        mean_12 = ts_mean(data["close"], 12)
        mean_24 = ts_mean(data["close"], 24)
        return (mean_3 + mean_6 + mean_12 + mean_24) / 4
