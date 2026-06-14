"""Real WorldQuant Alpha101 formula — Alpha081: (-1 * (rank(log(product(rank((rank(correlation(vwap, ts_sum(adv10, 50), 8))^4)), 15))) < rank(correlation(rank(vwap), rank(volume), 5))))"""
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
class Alpha081(AlphaFactor):
    """Alpha081: (-1 * (rank(log(product(rank((rank(correlation(vwap, sma(adv10, 50), 8))^4)), 15))) < rank(correlation(rank(vwap), rank(volume), 5))))"""

    @property
    def name(self) -> str:
        return "alpha081"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha081: (-1 * (rank(log(product(rank((rank(correlation(vwap, sma(adv10, 50), 8))^4)), 15))) < rank(correlation(rank(vwap), rank(volume), 5))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        adv10 = data["volume"].rolling(10).mean()
        corr = correlation(vwap, adv10.rolling(50).mean(), 8)
        r = rank(corr) ** 4
        prod = ts_product(r, 15)
        lp = np.log(prod.abs() + 1e-8)
        right = correlation(rank(vwap), rank(data["volume"]), 5)
        cond = rank(lp) < rank(right)
        return bool_to_float(cond, lp, right, sign=-1.0)
