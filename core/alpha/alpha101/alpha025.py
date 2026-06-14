"""Real WorldQuant Alpha101 formula — Alpha025: rank(-1 * ((close - delay(close, 5)) / delay(close, 5) * volume - (close - delay(close, 5)) / delay(close, 5)))"""
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
class Alpha025(AlphaFactor):
    """Alpha025: rank(-1 * ((close - delay(close, 5)) / delay(close, 5) * volume - (close - delay(close, 5)) / delay(close, 5)))"""

    @property
    def name(self) -> str:
        return "alpha025"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha025: rank(-1 * ((close - delay(close, 5)) / delay(close, 5) * volume - (close - delay(close, 5)) / delay(close, 5)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        ret5 = data["close"].pct_change(5)
        raw = ret5 * data["volume"] - ret5
        return rank(-raw)
