"""Real WorldQuant Alpha101 formula — Price Structure alpha126: (close + high + low) / 3"""
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
class Alpha126(AlphaFactor):
    """Price Structure alpha126: (close + high + low) / 3 — typical price"""

    @property
    def name(self) -> str:
        return "alpha126"

    @property
    def category(self) -> str:
        return "price_structure"

    @property
    def description(self) -> str:
        return "Price Structure alpha126: (close + high + low) / 3 — typical price"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return (data["close"] + data["high"] + data["low"]) / 3
