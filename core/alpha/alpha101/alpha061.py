"""Real WorldQuant Alpha101 formula — Alpha061: (rank((vwap - ts_min(vwap, 16.1219))) < rank(correlation(vwap, adv180, 17.9282)))"""
import numpy as np
import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .operators import (
    rank, ts_rank, ts_argmax, ts_argmin, ts_sum, ts_product,
    ts_min, ts_max, ts_mean, ts_std, ts_cov, correlation, covariance,
    scale, delay, delta, signedpower, decay_linear, signed_sqrt, bool_to_float,
)


@FactorRegistry.register
class Alpha061(AlphaFactor):
    """Alpha061: (rank((vwap - ts_min(vwap, 16))) < rank(correlation(vwap, adv180, 18)))"""

    @property
    def name(self) -> str:
        return "alpha061"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha061: (rank((vwap - ts_min(vwap, 16))) < rank(correlation(vwap, adv180, 18)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        adv180 = data["volume"].rolling(180, min_periods=20).mean()
        lhs = rank(vwap - ts_min(vwap, 16))
        rhs = rank(correlation(vwap, adv180, 18))
        return bool_to_float(lhs < rhs, lhs, rhs)
