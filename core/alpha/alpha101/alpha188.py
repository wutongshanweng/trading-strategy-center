"""Real WorldQuant Alpha101 formula — Momentum alpha188: (high - low - SMA(high - low, 11, 2)) / SMA(high - low, 11, 2) * 100"""
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
class Alpha188(AlphaFactor):
    """Momentum alpha188: (high - low - SMA(high - low, 11, 2)) / SMA(high - low, 11, 2) * 100"""

    @property
    def name(self) -> str:
        return "alpha188"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha188: (high - low - SMA(high - low, 11, 2)) / SMA(high - low, 11, 2) * 100"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        hl = data["high"] - data["low"]
        sma_hl = hl.ewm(alpha=2/12, adjust=False).mean()
        return ((hl - sma_hl) / (sma_hl + 1e-8)) * 100
