"""Real WorldQuant Alpha101 formula — alpha043"""
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
class Alpha043_en(AlphaFactor):
    """alpha043: ts_rank((volume/adv20),20)*ts_rank((-1*delta(close,7)),8)"""

    @property
    def name(self) -> str:
        return "alpha_en_043"

    @property
    def category(self) -> str:
        return "volume_momentum"

    @property
    def description(self) -> str:
        return "ts_rank((volume/adv20),20)*ts_rank((-1*delta(close,7)),8)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv20 = ts_mean(data["volume"], 20)
        vol_adv = data["volume"] / adv20
        ts_rank1 = ts_rank(vol_adv, 20)
        ts_rank2 = ts_rank(-1 * delta(data["close"], 7), 8)
        return ts_rank1 * ts_rank2
