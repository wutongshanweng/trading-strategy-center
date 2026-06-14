"""Real WorldQuant Alpha101 formula — Alpha065: ((rank(correlation(((open * 0.00817205) + (vwap * (1 - 0.00817205))), sum(adv60, 8.6911), 6.40374)) < rank((open - ts_min(open, 13.635)))) * -1)"""
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
class Alpha065(AlphaFactor):
    """Alpha065: ((rank(correlation(((open * 0.00817205) + (vwap * (1 - 0.00817205))), sma(adv60, 9), 6)) < rank((open - ts_min(open, 14)))) * -1)"""

    @property
    def name(self) -> str:
        return "alpha065"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha065: ((rank(correlation(((open * 0.00817205) + (vwap * (1 - 0.00817205))), sma(adv60, 9), 6)) < rank((open - ts_min(open, 14)))) * -1)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        adv60 = data["volume"].rolling(60, min_periods=5).mean()
        blended = data["open"] * 0.00817205 + vwap * 0.99182795
        corr = correlation(blended, adv60.rolling(9, min_periods=2).mean(), 6)
        omin = data["open"] - ts_min(data["open"], 14)
        return bool_to_float(rank(corr) < rank(omin), corr, omin, sign=-1.0)
