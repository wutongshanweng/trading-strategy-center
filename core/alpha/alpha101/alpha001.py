"""Real WorldQuant Alpha101 formula — Momentum alpha001: (rank(Ts_ArgMax(...)))"""
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
class Alpha001(AlphaFactor):
    """Momentum alpha001: (rank(Ts_ArgMax(SignedPower(...), 5)) - 0.5)"""

    @property
    def name(self) -> str:
        return "alpha001"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha001: (rank(Ts_ArgMax(SignedPower(...), 5)) - 0.5)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        ret = data["close"].pct_change()
        inner = ret.where(ret < 0, data["close"]).rolling(20).std()
        sp = signedpower(inner, 2.0)
        arg = ts_argmax(sp, 5)
        return rank(arg) - 0.5
