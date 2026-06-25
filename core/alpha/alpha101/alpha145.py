"""Real WorldQuant Alpha101 formula — Momentum alpha145: (mean(volume, 9) - mean(volume, 26)) / mean(volume, 12) * 100"""
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
class Alpha145(AlphaFactor):
    """Momentum alpha145: (mean(volume, 9) - mean(volume, 26)) / mean(volume, 12) * 100"""

    @property
    def name(self) -> str:
        return "alpha145"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha145: (mean(volume, 9) - mean(volume, 26)) / mean(volume, 12) * 100"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        mean_vol_9 = ts_mean(data["volume"], 9)
        mean_vol_26 = ts_mean(data["volume"], 26)
        mean_vol_12 = ts_mean(data["volume"], 12)
        return ((mean_vol_9 - mean_vol_26) / (mean_vol_12 + 1e-8)) * 100
