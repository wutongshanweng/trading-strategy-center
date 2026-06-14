"""Real WorldQuant Alpha101 formula — Alpha011: ((rank(Ts_LogMax(rank(((close - open) / open)), 5)) + rank(Ts_LogMin(rank(((close - open) / open)), 5))) / 2)"""
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
class Alpha011(AlphaFactor):
    """Alpha011: ((rank(Ts_LogMax(rank(((close - open) / open)), 5)) + rank(Ts_LogMin(rank(((close - open) / open)), 5))) / 2)"""

    @property
    def name(self) -> str:
        return "alpha011"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha011: ((rank(Ts_LogMax(rank(((close - open) / open)), 5)) + rank(Ts_LogMin(rank(((close - open) / open)), 5))) / 2)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        oc = (data["close"] - data["open"]) / (data["open"] + 1e-8)
        r = rank(oc)
        tmax = ts_max(r, 5)
        tmin = ts_min(r, 5)
        return (tmax + tmin) / 2
