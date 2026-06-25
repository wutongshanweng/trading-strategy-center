"""Real WorldQuant Alpha101 formula — alpha024"""
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
class Alpha024_en(AlphaFactor):
    """alpha024: (((delta((sum(close,100)/100),100)/delay(close,100))<0.05)?(-1*(close-ts_min(close,100))):(-1*delta(close,3)))"""

    @property
    def name(self) -> str:
        return "alpha_en_024"

    @property
    def category(self) -> str:
        return "mean_reversion"

    @property
    def description(self) -> str:
        return "(((delta((sum(close,100)/100),100)/delay(close,100))<0.05)?(-1*(close-ts_min(close,100))):(-1*delta(close,3)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        avg_close_100 = ts_sum(data["close"], 100) / 100
        delta_avg = delta(avg_close_100, 100)
        delayed_close = delay(data["close"], 100)
        ratio = delta_avg / delayed_close
        cond = ratio < 0.05
        part1 = -1 * (data["close"] - ts_min(data["close"], 100))
        part2 = -1 * delta(data["close"], 3)
        return pd.Series(np.where(cond, part1, part2), index=data.index)
