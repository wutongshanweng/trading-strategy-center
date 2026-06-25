"""Real WorldQuant Alpha101 formula — alpha059"""
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
class Alpha059_en(AlphaFactor):
    """alpha059: -1*ts_rank(decay_linear(correlation(((vwap*0.73)+(vwap*(1-0.73))),volume,4.3),16.2),8.2)"""

    @property
    def name(self) -> str:
        return "alpha_en_059"

    @property
    def category(self) -> str:
        return "correlation"

    @property
    def description(self) -> str:
        return "-1*ts_rank(decay_linear(correlation(((vwap*0.73)+(vwap*(1-0.73))),volume,4.3),16.2),8.2)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap_weighted = (data["vwap"] * 0.73) + (data["vwap"] * 0.27)
        corr = correlation(vwap_weighted, data["volume"], 4)
        decay_corr = decay_linear(corr, 16)
        ts_rank_val = ts_rank(decay_corr, 8)
        return -1 * ts_rank_val
