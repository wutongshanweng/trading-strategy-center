"""Real WorldQuant Alpha101 formula — alpha049"""
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
class Alpha049_en(AlphaFactor):
    """alpha049: (((((delay(close,20)-delay(close,10))/10)-((delay(close,10)-close)/10))<-0.1)?1:((-1*1)*(close-delay(close,1)))"""

    @property
    def name(self) -> str:
        return "alpha_en_049"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "(((((delay(close,20)-delay(close,10))/10)-((delay(close,10)-close)/10))<-0.1)?1:((-1*1)*(close-delay(close,1)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        delay10 = delay(data["close"], 10)
        delay20 = delay(data["close"], 20)
        momentum = ((delay20 - delay10) / 10) - ((delay10 - data["close"]) / 10)
        cond = momentum < -0.1
        result = pd.Series(np.where(cond, 1.0, -1 * (data["close"] - delay(data["close"], 1))),
                         index=data.index)
        return result
