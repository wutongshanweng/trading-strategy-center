"""Real WorldQuant Alpha101 formula — Alpha060: (0 - (1 * ((2 * scale(rank(((((close - low) - (high - close)) / (high - low)) * volume)))) - scale(rank(ts_argmax(close, 10))))))"""
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
class Alpha060(AlphaFactor):
    """Alpha060: (0 - (1 * ((2 * scale(rank(((((close - low) - (high - close)) / (high - low)) * volume)))) - scale(rank(ts_argmax(close, 10))))))"""

    @property
    def name(self) -> str:
        return "alpha060"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha060: (0 - (1 * ((2 * scale(rank(((((close - low) - (high - close)) / (high - low)) * volume)))) - scale(rank(ts_argmax(close, 10))))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        divisor = (data["high"] - data["low"]).replace(0, 1e-8)
        inner = ((data["close"] - data["low"]) - (data["high"] - data["close"])) * data["volume"] / divisor
        return 0 - ((2 * scale(rank(inner))) - scale(rank(ts_argmax(data["close"], 10))))
