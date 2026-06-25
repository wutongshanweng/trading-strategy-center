"""Real WorldQuant Alpha101 formula — alpha017"""
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
class Alpha017_en(AlphaFactor):
    """alpha017: ((-1*rank(ts_rank(close,10)))*rank(delta(delta(close,1),1)))*rank(ts_rank((volume/adv20),5))"""

    @property
    def name(self) -> str:
        return "alpha_en_017"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "((-1*rank(ts_rank(close,10)))*rank(delta(delta(close,1),1)))*rank(ts_rank((volume/adv20),5))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv20 = ts_mean(data["volume"], 20)
        ts_rank_close = ts_rank(data["close"], 10)
        rank_ts_rank_close = rank(ts_rank_close)
        delta2_close = delta(delta(data["close"], 1), 1)
        rank_delta2 = rank(delta2_close)
        vol_adv = data["volume"] / adv20
        ts_rank_vol = ts_rank(vol_adv, 5)
        rank_vol = rank(ts_rank_vol)
        return (-1 * rank_ts_rank_close) * rank_delta2 * rank_vol
