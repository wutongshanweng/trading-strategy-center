"""Real WorldQuant Alpha101 formula — alpha019"""
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
class Alpha019_en(AlphaFactor):
    """alpha019: (-1*sign((close-delay(close,7))+delta(close,7)))*(1+rank(1+sum(returns,250)))"""

    @property
    def name(self) -> str:
        return "alpha_en_019"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "(-1*sign((close-delay(close,7))+delta(close,7)))*(1+rank(1+sum(returns,250)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        returns = data["close"].pct_change()
        delayed_close = delay(data["close"], 7)
        delta_close_7 = delta(data["close"], 7)
        sign_arg = (data["close"] - delayed_close) + delta_close_7
        sign_val = -1 * np.sign(sign_arg)
        sum_ret_250 = ts_sum(returns, 250)
        rank_part = rank(1 + sum_ret_250)
        return sign_val * (1 + rank_part)
