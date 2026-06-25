"""Real WorldQuant Alpha101 formula — alpha086"""
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
class Alpha086_en(AlphaFactor):
    """alpha086: ((ts_rank(correlation(close,sum(adv20,14.7),6),20.4)<rank(((open+close)-(vwap+open))))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_086"

    @property
    def category(self) -> str:
        return "comparison"

    @property
    def description(self) -> str:
        return "((ts_rank(correlation(close,sum(adv20,14.7),6),20.4)<rank(((open+close)-(vwap+open))))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv20 = ts_mean(data["volume"], 20)
        sum_adv = ts_sum(adv20, 15)
        corr = correlation(data["close"], sum_adv, 6)
        ts_rank1 = ts_rank(corr, 20)
        inner = (data["open"] + data["close"]) - (data["vwap"] + data["open"])
        rank2 = rank(inner)
        cond = ts_rank1 < rank2
        return pd.Series(np.where(cond, -1.0, 0.0), index=data.index)
