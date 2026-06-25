"""Real WorldQuant Alpha101 formula — alpha021"""
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
class Alpha021_en(AlphaFactor):
    """alpha021: (((sum(close,8)/8+stddev(close,8))<(sum(close,2)/2))?(-1*1):(((sum(close,2)/2)<((sum(close,8)/8)-stddev(close,8)))?1:((1<(volume/adv20))?1:(-1*1))))"""

    @property
    def name(self) -> str:
        return "alpha_en_021"

    @property
    def category(self) -> str:
        return "mean_reversion"

    @property
    def description(self) -> str:
        return "(((sum(close,8)/8+stddev(close,8))<(sum(close,2)/2))?(-1*1):(((sum(close,2)/2)<((sum(close,8)/8)-stddev(close,8)))?1:((1<(volume/adv20))?1:(-1*1))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv20 = ts_mean(data["volume"], 20)
        sum_close_8 = ts_sum(data["close"], 8)
        avg_close_8 = sum_close_8 / 8
        stddev_close_8 = ts_std(data["close"], 8)
        sum_close_2 = ts_sum(data["close"], 2)
        avg_close_2 = sum_close_2 / 2
        upper = avg_close_8 + stddev_close_8
        lower = avg_close_8 - stddev_close_8

        cond1 = upper < avg_close_2
        cond2 = avg_close_2 < lower
        cond3 = 1 < (data["volume"] / adv20)

        result = pd.Series(np.where(cond1, -1.0,
                                   np.where(cond2, 1.0,
                                           np.where(cond3, 1.0, -1.0))),
                         index=data.index)
        return result
