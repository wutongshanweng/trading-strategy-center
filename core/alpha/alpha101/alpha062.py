"""Real WorldQuant Alpha101 formula — Alpha062: ((rank(correlation(vwap, sum(adv20, 22.4101), 9.91009)) < rank(((rank(open) + rank(open)) < (rank(((high + low) / 2)) + rank(high))))) * -1)"""
import numpy as np
import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .operators import (
    rank, ts_rank, ts_argmax, ts_argmin, ts_sum, ts_product,
    ts_min, ts_max, ts_mean, ts_std, ts_cov, correlation, covariance,
    scale, delay, delta, signedpower, decay_linear, signed_sqrt,
    bool_to_float,
)


@FactorRegistry.register
class Alpha062(AlphaFactor):
    """Alpha062: ((rank(correlation(vwap, sma(adv20, 22), 10)) < rank(((rank(open) + rank(open)) < (rank(((high + low) / 2)) + rank(high))))) * -1)"""

    @property
    def name(self) -> str:
        return "alpha062"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha062: ((rank(correlation(vwap, sma(adv20, 22), 10)) < rank(((rank(open) + rank(open)) < (rank(((high + low) / 2)) + rank(high))))) * -1)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        adv20 = data["volume"].rolling(20).mean()
        cond_inner = (rank(data["open"]) + rank(data["open"])) < (rank((data["high"] + data["low"]) / 2) + rank(data["high"]))
        corr = correlation(vwap, adv20.rolling(22).mean(), 10)
        cond = rank(corr) < rank(cond_inner.astype(float))
        return bool_to_float(cond, corr, sign=-1.0)
