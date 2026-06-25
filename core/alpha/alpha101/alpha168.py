"""Real WorldQuant Alpha101 formula — Momentum alpha168: -volume / mean(volume, 20)"""
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
class Alpha168(AlphaFactor):
    """Momentum alpha168: -volume / mean(volume, 20) — negative volume relative"""

    @property
    def name(self) -> str:
        return "alpha168"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha168: -volume / mean(volume, 20) — negative volume relative"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        mean_vol = ts_mean(data["volume"], 20)
        return -data["volume"] / (mean_vol + 1e-8)
