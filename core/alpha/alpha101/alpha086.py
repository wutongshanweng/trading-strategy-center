"""Real WorldQuant Alpha101 formula — Alpha086: (-1 * (ts_rank(correlation(close, sma(adv20, 15), 6), 20) < rank((open + close) - (vwap + open))))"""
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
class Alpha086(AlphaFactor):
    """Alpha086: (-1 * (ts_rank(correlation(close, sma(adv20, 15), 6), 20) < rank((open + close) - (vwap + open))))"""

    @property
    def name(self) -> str:
        return "alpha086"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha086: (-1 * (ts_rank(correlation(close, sma(adv20, 15), 6), 20) < rank((open + close) - (vwap + open))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        adv20 = data["volume"].rolling(20).mean()
        corr = correlation(data["close"], adv20.rolling(15).mean(), 6)
        left = ts_rank(corr, 20)
        right = rank((data["open"] + data["close"]) - (vwap + data["open"]))
        cond = left < right
        return bool_to_float(cond, left, vwap, sign=-1.0)
