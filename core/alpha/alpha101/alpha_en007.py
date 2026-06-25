"""Real WorldQuant Alpha101 formula — alpha007"""
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
class Alpha007_en(AlphaFactor):
    """alpha007: (adv20<volume)?((-1*ts_rank(abs(delta(close,7)),60))*sign(delta(close,7))):(-1*1)"""

    @property
    def name(self) -> str:
        return "alpha_en_007"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "(adv20<volume)?((-1*ts_rank(abs(delta(close,7)),60))*sign(delta(close,7))):(-1*1)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv20 = ts_mean(data["volume"], 20)
        cond = adv20 < data["volume"]
        delta_close_7 = delta(data["close"], 7)
        part1 = -1 * ts_rank(abs(delta_close_7), 60) * np.sign(delta_close_7)
        part2 = -1.0
        return pd.Series(np.where(cond, part1, part2), index=data.index)
