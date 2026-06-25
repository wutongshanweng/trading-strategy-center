"""Real WorldQuant Alpha101 formula — Volume alpha102: SMA(MAX(VOLUME,0),6,1)"""
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
class Alpha102(AlphaFactor):
    """Volume alpha102: SMA(MAX(VOLUME,0),6,1) — volume positive part 6-day SMA"""

    @property
    def name(self) -> str:
        return "alpha102"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Volume alpha102: SMA(MAX(VOLUME,0),6,1) — volume positive part 6-day SMA"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vol = data["volume"].copy()
        pos_vol = vol.where(vol > 0, 0)
        return pos_vol.ewm(alpha=1/6, adjust=False).mean()
