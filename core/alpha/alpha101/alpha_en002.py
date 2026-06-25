"""Real WorldQuant Alpha101 formula — alpha002"""
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
class Alpha002_en(AlphaFactor):
    """alpha002: -1*correlation(rank(delta(log(volume),2)),rank((close-open)/open),6)"""

    @property
    def name(self) -> str:
        return "alpha_en_002"

    @property
    def category(self) -> str:
        return "correlation"

    @property
    def description(self) -> str:
        return "-1*correlation(rank(delta(log(volume),2)),rank((close-open)/open),6)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        log_vol = np.log(data["volume"])
        d_log_vol = delta(log_vol, 2)
        rank_d_log_vol = rank(d_log_vol)
        close_open_ret = (data["close"] - data["open"]) / data["open"]
        rank_ret = rank(close_open_ret)
        corr = correlation(rank_d_log_vol, rank_ret, 6)
        return -1 * corr
