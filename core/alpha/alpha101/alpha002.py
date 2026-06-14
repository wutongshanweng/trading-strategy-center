"""Real WorldQuant Alpha101 formula — Alpha002: (-1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6))"""
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
class Alpha002(AlphaFactor):
    """Alpha002: (-1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6))"""

    @property
    def name(self) -> str:
        return "alpha002"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha002: (-1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        v_delta = delta(np.log(data["volume"] + 1), 2)
        oc_ratio = (data["close"] - data["open"]) / (data["open"] + 1e-8)
        return -1 * correlation(rank(v_delta), rank(oc_ratio), 6)
