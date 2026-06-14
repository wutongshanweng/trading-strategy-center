"""Real WorldQuant Alpha101 formula — Alpha057: (0 - (1 * ((close - vwap) / decay_linear(rank(ts_argmax(close, 30)), 2))))"""
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
class Alpha057(AlphaFactor):
    """Alpha057: (0 - (1 * ((close - vwap) / decay_linear(rank(ts_argmax(close, 30)), 2))))"""

    @property
    def name(self) -> str:
        return "alpha057"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha057: (0 - (1 * ((close - vwap) / decay_linear(rank(ts_argmax(close, 30)), 2))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        dl = decay_linear(rank(ts_argmax(data["close"], 30)).to_frame(), 2).iloc[:, 0]
        return 0 - (1 * ((data["close"] - vwap) / dl))
