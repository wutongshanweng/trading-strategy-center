"""Real WorldQuant Alpha101 formula — Alpha064: ((rank(correlation(sum(((open * 0.178404) + (low * (1 - 0.178404))), 12.7054), sum(adv120, 12.7054), 16.6208)) < rank(delta(((((high + low) / 2) * 0.178404) + (vwap * (1 - 0.178404))), 3.69741))) * -1)"""
import numpy as np
import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .operators import (
    rank, ts_rank, ts_argmax, ts_argmin, ts_sum, ts_product,
    ts_min, ts_max, ts_mean, ts_std, ts_cov, correlation, covariance,
    scale, delay, delta, signedpower, decay_linear, signed_sqrt, bool_to_float,
)


@FactorRegistry.register
class Alpha064(AlphaFactor):
    """Alpha064: ((rank(correlation(sma(((open * 0.178404) + (low * (1 - 0.178404))), 13), sma(adv120, 13), 17)) < rank(delta(((((high + low) / 2) * 0.178404) + (vwap * (1 - 0.178404))), 4))) * -1)"""

    @property
    def name(self) -> str:
        return "alpha064"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha064: ((rank(correlation(sma(((open * 0.178404) + (low * (1 - 0.178404))), 13), sma(adv120, 13), 17)) < rank(delta(((((high + low) / 2) * 0.178404) + (vwap * (1 - 0.178404))), 4))) * -1)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        adv120 = data["volume"].rolling(120, min_periods=20).mean()
        blended_open = data["open"] * 0.178404 + data["low"] * 0.821596
        corr = correlation(blended_open.rolling(13).mean(), adv120.rolling(13).mean(), 17)
        blended_hl = ((data["high"] + data["low"]) / 2) * 0.178404 + vwap * 0.821596
        d = delta(blended_hl, 4)
        return bool_to_float(rank(corr) < rank(d), corr, d, sign=-1.0)
