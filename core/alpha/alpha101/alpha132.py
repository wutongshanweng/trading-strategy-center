"""Real WorldQuant Alpha101 formula — Volume alpha132: mean(amount, 20)"""
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
class Alpha132(AlphaFactor):
    """Volume alpha132: mean(amount, 20) — average trading amount over 20 periods"""

    @property
    def name(self) -> str:
        return "alpha132"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Volume alpha132: mean(amount, 20) — average trading amount over 20 periods"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        if "amount" in data.columns:
            return ts_mean(data["amount"], 20)
        else:
            # Fallback to volume * close as proxy for amount
            return ts_mean(data["volume"] * data["close"], 20)
