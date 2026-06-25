"""Real WorldQuant Alpha101 formula — alpha058"""
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
class Alpha058_en(AlphaFactor):
    """alpha058: -1*ts_rank(decay_linear(correlation(vwap,mean(volume,3.9),7.9),5.5),8.2)"""

    @property
    def name(self) -> str:
        return "alpha_en_058"

    @property
    def category(self) -> str:
        return "correlation"

    @property
    def description(self) -> str:
        return "-1*ts_rank(decay_linear(correlation(vwap,mean(volume,3.9),7.9),5.5),8.2)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        mean_vol = ts_mean(data["volume"], 4)
        corr = correlation(data["vwap"], mean_vol, 8)
        decay_corr = decay_linear(corr, 6)
        ts_rank_val = ts_rank(decay_corr, 8)
        return -1 * ts_rank_val
