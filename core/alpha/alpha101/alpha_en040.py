"""Real WorldQuant Alpha101 formula — alpha040"""
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
class Alpha040_en(AlphaFactor):
    """alpha040: ((-1*rank(stddev(high,10)))*correlation(high,volume,10))"""

    @property
    def name(self) -> str:
        return "alpha_en_040"

    @property
    def category(self) -> str:
        return "correlation"

    @property
    def description(self) -> str:
        return "((-1*rank(stddev(high,10)))*correlation(high,volume,10))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        stddev_high = ts_std(data["high"], 10)
        rank_stddev = -1 * rank(stddev_high)
        corr = correlation(data["high"], data["volume"], 10)
        return rank_stddev * corr
