"""Real WorldQuant Alpha101 formula — Alpha056: (0 - (1 * (rank((sma(returns, 10) / sma(sma(returns, 2), 3))) * rank((returns * cap)))))
Note: Requires market cap data. Simplified implementation uses volume as proxy."""
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
class Alpha056(AlphaFactor):
    """Alpha056: Composite momentum with volume proxy"""

    @property
    def name(self) -> str:
        return "alpha056"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Alpha056: Composite momentum with volume proxy"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        ret = data["close"].pct_change()
        ratio = ret.rolling(10).mean() / ret.rolling(2).mean().rolling(3).mean()
        return 0 - (rank(ratio) * rank(data["volume"]))
