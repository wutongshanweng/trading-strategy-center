"""Real WorldQuant Alpha101 formula — Alpha045: (-1 * ((rank((sma(delay(close, 5), 20))) * correlation(close, volume, 2)) * rank(correlation(ts_sum(close, 5), ts_sum(close, 20), 2))))"""
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
class Alpha045(AlphaFactor):
    """Alpha045: (-1 * ((rank((sma(delay(close, 5), 20))) * correlation(close, volume, 2)) * rank(correlation(ts_sum(close, 5), ts_sum(close, 20), 2))))"""

    @property
    def name(self) -> str:
        return "alpha045"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha045: (-1 * ((rank((sma(delay(close, 5), 20))) * correlation(close, volume, 2)) * rank(correlation(ts_sum(close, 5), ts_sum(close, 20), 2))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        df = correlation(data["close"], data["volume"], 2)
        df = df.replace([-np.inf, np.inf], 0).fillna(0)
        return -1 * (rank(data["close"].shift(5).rolling(20).mean()) * df *
                     rank(correlation(ts_sum(data["close"], 5), ts_sum(data["close"], 20), 2)))
