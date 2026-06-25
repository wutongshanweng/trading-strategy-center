"""Real WorldQuant Alpha101 formula — alpha046"""
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
class Alpha046_en(AlphaFactor):
    """alpha046: ((0.25<(((delay(close,20)-delay(close,10))/10)-((delay(close,10)-close)/10)))?(-1*1):(((((delay(close,20)-delay(close,10))/10)-((delay(close,10)-close)/10))<0)?1:((-1*1)*(close-delay(close,1)))))"""

    @property
    def name(self) -> str:
        return "alpha_en_046"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "((0.25<(((delay(close,20)-delay(close,10))/10)-((delay(close,10)-close)/10)))?(-1*1):(((((delay(close,20)-delay(close,10))/10)-((delay(close,10)-close)/10))<0)?1:((-1*1)*(close-delay(close,1)))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        delay10 = delay(data["close"], 10)
        delay20 = delay(data["close"], 20)
        momentum = ((delay20 - delay10) / 10) - ((delay10 - data["close"]) / 10)
        cond1 = momentum > 0.25
        cond2 = momentum < 0
        result = pd.Series(np.where(cond1, -1.0,
                                   np.where(cond2, 1.0, -1 * (data["close"] - delay(data["close"], 1)))),
                         index=data.index)
        return result
