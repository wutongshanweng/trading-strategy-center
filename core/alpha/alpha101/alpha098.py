"""Real WorldQuant Alpha101 formula — Alpha098: (rank(decay_linear(correlation(vwap, sma(adv5, 26), 5), 7)) - rank(decay_linear(ts_rank(ts_argmin(correlation(rank(open), rank(adv15), 21), 9), 7), 8)))"""
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
class Alpha098(AlphaFactor):
    """Alpha098: (rank(decay_linear(correlation(vwap, sma(adv5, 26), 5), 7)) - rank(decay_linear(ts_rank(ts_argmin(correlation(rank(open), rank(adv15), 21), 9), 7), 8)))"""

    @property
    def name(self) -> str:
        return "alpha098"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha098: (rank(decay_linear(correlation(vwap, sma(adv5, 26), 5), 7)) - rank(decay_linear(ts_rank(ts_argmin(correlation(rank(open), rank(adv15), 21), 9), 7), 8)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        adv5 = data["volume"].rolling(5).mean()
        adv15 = data["volume"].rolling(15).mean()
        corr1 = correlation(vwap, adv5.rolling(26).mean(), 5)
        dl1 = decay_linear(corr1.to_frame(), 7).iloc[:, 0]
        t1 = rank(dl1)
        corr2 = correlation(rank(data["open"]), rank(adv15), 21)
        argmin_val = ts_argmin(corr2, 9)
        r2 = ts_rank(argmin_val, 7)
        dl2 = decay_linear(r2.to_frame(), 8).iloc[:, 0]
        t2 = rank(dl2)
        return t1 - t2
