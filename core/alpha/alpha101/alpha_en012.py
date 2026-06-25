"""Real WorldQuant Alpha101 formula — alpha012"""
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
class Alpha012_en(AlphaFactor):
    """alpha012: sign(delta(volume,1))*(-1*delta(close,1))"""

    @property
    def name(self) -> str:
        return "alpha_en_012"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "sign(delta(volume,1))*(-1*delta(close,1))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        delta_vol = delta(data["volume"], 1)
        delta_close = delta(data["close"], 1)
        return np.sign(delta_vol) * (-1 * delta_close)
