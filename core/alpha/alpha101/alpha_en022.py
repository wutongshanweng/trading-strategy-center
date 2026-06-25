"""Real WorldQuant Alpha101 formula — alpha022"""
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
class Alpha022_en(AlphaFactor):
    """alpha022: -1*(delta(correlation(high,volume,5),5)*rank(stddev(close,20)))"""

    @property
    def name(self) -> str:
        return "alpha_en_022"

    @property
    def category(self) -> str:
        return "correlation"

    @property
    def description(self) -> str:
        return "-1*(delta(correlation(high,volume,5),5)*rank(stddev(close,20)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        corr = correlation(data["high"], data["volume"], 5)
        delta_corr = delta(corr, 5)
        stddev_close = ts_std(data["close"], 20)
        rank_stddev = rank(stddev_close)
        return -1 * (delta_corr * rank_stddev)
