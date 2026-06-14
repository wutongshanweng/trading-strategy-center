"""Real WorldQuant Alpha101 formula — Alpha019: ((-1 * sign(((close - delay(close, 7)) + (close - delay(close, 14))))) * (1 + rank(1 - rank(1 + sum(returns, 250)))))"""
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
class Alpha019(AlphaFactor):
    """Alpha019: ((-1 * sign(((close - delay(close, 7)) + (close - delay(close, 14))))) * (1 + rank(1 - rank(1 + sum(returns, 250)))))"""

    @property
    def name(self) -> str:
        return "alpha019"

    @property
    def category(self) -> str:
        return "price_momentum"

    @property
    def description(self) -> str:
        return "Alpha019: ((-1 * sign(((close - delay(close, 7)) + (close - delay(close, 14))))) * (1 + rank(1 - rank(1 + sum(returns, 250)))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        ret = data["close"].pct_change()
        mom7 = data["close"] - delay(data["close"], 7)
        mom14 = data["close"] - delay(data["close"], 14)
        s = np.sign(mom7 + mom14)
        sr250 = ret.rolling(250).sum()
        return -1 * s * (1 + rank(1 - rank(1 + sr250)))
