"""Real WorldQuant Alpha101 formula — Alpha066: ((rank(decay_linear(delta(vwap, 3.51013), 7.23052)) + Ts_Rank(decay_linear(((((low * 0.96633) + (low * (1 - 0.96633))) - vwap) / (open - ((high + low) / 2))), 11.4157), 6.72611)) * -1)"""
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
class Alpha066(AlphaFactor):
    """Alpha066: ((rank(decay_linear(delta(vwap, 4), 7)) + ts_rank(decay_linear((((low) - vwap) / (open - ((high + low) / 2))), 11), 7)) * -1)"""

    @property
    def name(self) -> str:
        return "alpha066"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha066: ((rank(decay_linear(delta(vwap, 4), 7)) + ts_rank(decay_linear((((low) - vwap) / (open - ((high + low) / 2))), 11), 7)) * -1)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        dl1 = decay_linear(delta(vwap, 4).to_frame(), 7).iloc[:, 0]
        divisor = data["open"] - ((data["high"] + data["low"]) / 2)
        numerator = data["low"] - vwap
        dl2 = decay_linear((numerator / divisor.replace(0, 1e-8)).to_frame(), 11).iloc[:, 0]
        return (rank(dl1) + ts_rank(dl2, 7)) * -1
