"""Real WorldQuant Alpha101 formula — Alpha028: scale(((close - ts_min(close, 100)) / (ts_max(close, 100) - ts_min(close, 100) + 1e-8)))"""
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
class Alpha028(AlphaFactor):
    """Alpha028: scale(((close - ts_min(close, 100)) / (ts_max(close, 100) - ts_min(close, 100) + 1e-8)))"""

    @property
    def name(self) -> str:
        return "alpha028"

    @property
    def category(self) -> str:
        return "price_momentum"

    @property
    def description(self) -> str:
        return "Alpha028: scale(((close - ts_min(close, 100)) / (ts_max(close, 100) - ts_min(close, 100) + 1e-8)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        cmin = ts_min(data["close"], 100)
        cmax = ts_max(data["close"], 100)
        raw = (data["close"] - cmin) / (cmax - cmin + 1e-8)
        return scale(raw)
