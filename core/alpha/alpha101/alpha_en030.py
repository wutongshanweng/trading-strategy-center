"""Real WorldQuant Alpha101 formula — alpha030"""
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
class Alpha030_en(AlphaFactor):
    """alpha030: (((1-rank(((sign((close-delay(close,1)))+sign((delay(close,1)-delay(close,2))))+sign((delay(close,2)-delay(close,3)))))))*sum(volume,5))/sum(volume,20)"""

    @property
    def name(self) -> str:
        return "alpha_en_030"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "(((1-rank(((sign((close-delay(close,1)))+sign((delay(close,1)-delay(close,2))))+sign((delay(close,2)-delay(close,3)))))))*sum(volume,5))/sum(volume,20)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        delay1 = delay(data["close"], 1)
        delay2 = delay(data["close"], 2)
        delay3 = delay(data["close"], 3)
        sign1 = np.sign(data["close"] - delay1)
        sign2 = np.sign(delay1 - delay2)
        sign3 = np.sign(delay2 - delay3)
        sum_signs = sign1 + sign2 + sign3
        rank_part = 1 - rank(sum_signs)
        sum_vol_5 = ts_sum(data["volume"], 5)
        sum_vol_20 = ts_sum(data["volume"], 20)
        return rank_part * sum_vol_5 / sum_vol_20
