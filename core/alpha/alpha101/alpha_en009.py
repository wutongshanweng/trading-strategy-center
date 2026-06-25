"""Real WorldQuant Alpha101 formula — alpha009"""
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
class Alpha009_en(AlphaFactor):
    """alpha009: (0<ts_min(delta(close,1),5))?delta(close,1):((ts_max(delta(close,1),5)<0)?delta(close,1):(-1*delta(close,1)))"""

    @property
    def name(self) -> str:
        return "alpha_en_009"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "(0<ts_min(delta(close,1),5))?delta(close,1):((ts_max(delta(close,1),5)<0)?delta(close,1):(-1*delta(close,1)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        delta_close = delta(data["close"], 1)
        ts_min_delta = ts_min(delta_close, 5)
        ts_max_delta = ts_max(delta_close, 5)
        cond1 = ts_min_delta > 0
        cond2 = ts_max_delta < 0
        result = pd.Series(np.where(cond1, delta_close,
                                    np.where(cond2, delta_close, -1 * delta_close)),
                          index=data.index)
        return result
