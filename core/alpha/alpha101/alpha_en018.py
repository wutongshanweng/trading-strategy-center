"""Real WorldQuant Alpha101 formula — alpha018"""
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
class Alpha018_en(AlphaFactor):
    """alpha018: -1*rank(((stddev(abs((close-open)),5)+(close-open))+correlation(close,open,10)))"""

    @property
    def name(self) -> str:
        return "alpha_en_018"

    @property
    def category(self) -> str:
        return "volatility"

    @property
    def description(self) -> str:
        return "-1*rank(((stddev(abs((close-open)),5)+(close-open))+correlation(close,open,10)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        close_open_diff = data["close"] - data["open"]
        stddev_diff = ts_std(abs(close_open_diff), 5)
        corr = correlation(data["close"], data["open"], 10)
        inner = stddev_diff + close_open_diff + corr
        return -1 * rank(inner)
