"""Real WorldQuant Alpha101 formula — alpha084"""
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
class Alpha084_en(AlphaFactor):
    """alpha084: signedpower(ts_rank((vwap-ts_max(vwap,15.3)),20.7),delta(close,4.97))"""

    @property
    def name(self) -> str:
        return "alpha_en_084"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "signedpower(ts_rank((vwap-ts_max(vwap,15.3)),20.7),delta(close,4.97))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap_max = data["vwap"] - ts_max(data["vwap"], 15)
        ts_rank_val = ts_rank(vwap_max, 21)
        delta_close = delta(data["close"], 5)
        return signedpower(ts_rank_val, delta_close)
