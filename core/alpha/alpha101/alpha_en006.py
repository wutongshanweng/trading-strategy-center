"""Real WorldQuant Alpha101 formula — alpha006"""
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
class Alpha006_en(AlphaFactor):
    """alpha006: -1*correlation(open,volume,10)"""

    @property
    def name(self) -> str:
        return "alpha_en_006"

    @property
    def category(self) -> str:
        return "correlation"

    @property
    def description(self) -> str:
        return "-1*correlation(open,volume,10)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        corr = correlation(data["open"], data["volume"], 10)
        return -1 * corr
