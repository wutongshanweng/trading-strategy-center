"""Real WorldQuant Alpha101 formula — Alpha067: Requires proprietary industry data. Simplified momentum-based implementation."""
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
class Alpha067(AlphaFactor):
    """Alpha067: Momentum-volatility composite (simplified)"""

    @property
    def name(self) -> str:
        return "alpha067"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Alpha067: Momentum-volatility composite (simplified)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        ret = data["close"].pct_change()
        mom = ret.rolling(20).mean()
        vol = ts_std(ret, 20) + 1e-8
        return rank(mom / vol) * rank(data["volume"])
