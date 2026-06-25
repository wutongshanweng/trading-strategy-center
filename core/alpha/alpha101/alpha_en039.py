"""Real WorldQuant Alpha101 formula — alpha039"""
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
class Alpha039_en(AlphaFactor):
    """alpha039: (-1*rank((delta(close,7)*(1-rank(decay_linear((volume/adv20),9))))))*(1+rank(sum(returns,250)))"""

    @property
    def name(self) -> str:
        return "alpha_en_039"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "(-1*rank((delta(close,7)*(1-rank(decay_linear((volume/adv20),9))))))*(1+rank(sum(returns,250)))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        returns = data["close"].pct_change()
        adv20 = ts_mean(data["volume"], 20)
        delta_close_7 = delta(data["close"], 7)
        vol_adv = data["volume"] / adv20
        decay_val = decay_linear(vol_adv, 9)
        rank_decay = rank(decay_val)
        inner = delta_close_7 * (1 - rank_decay)
        rank_inner = -1 * rank(inner)
        sum_ret_250 = ts_sum(returns, 250)
        rank_sum_ret = 1 + rank(sum_ret_250)
        return rank_inner * rank_sum_ret
