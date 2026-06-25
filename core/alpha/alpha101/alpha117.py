"""Real WorldQuant Alpha101 formula — Momentum alpha117: ts_rank(volume, 32) * (1 - ts_rank((close + high - low), 16)) * (1 - ts_rank(returns, 32))"""
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
class Alpha117(AlphaFactor):
    """Momentum alpha117: ts_rank(volume, 32) * (1 - ts_rank((close + high - low), 16)) * (1 - ts_rank(returns, 32))"""

    @property
    def name(self) -> str:
        return "alpha117"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha117: ts_rank(volume, 32) * (1 - ts_rank((close + high - low), 16)) * (1 - ts_rank(returns, 32))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        returns = data["close"].pct_change()
        hl = data["close"] + data["high"] - data["low"]
        ts_rank_vol = ts_rank(data["volume"], 32)
        ts_rank_hl = ts_rank(hl, 16)
        ts_rank_ret = ts_rank(returns, 32)
        return ts_rank_vol * (1 - ts_rank_hl) * (1 - ts_rank_ret)
