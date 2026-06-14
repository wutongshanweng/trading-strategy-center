"""Real WorldQuant Alpha101 formula — Alpha047: ((((rank((1 / close)) * volume) / adv20) * ((high * rank((high - close))) / (sma(high, 5) / 5))) - rank((vwap - delay(vwap, 5))))"""
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
class Alpha047(AlphaFactor):
    """Alpha047: ((((rank((1 / close)) * volume) / adv20) * ((high * rank((high - close))) / (sma(high, 5) / 5))) - rank((vwap - delay(vwap, 5))))"""

    @property
    def name(self) -> str:
        return "alpha047"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha047: ((((rank((1 / close)) * volume) / adv20) * ((high * rank((high - close))) / (sma(high, 5) / 5))) - rank((vwap - delay(vwap, 5))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv20 = data["volume"].rolling(20).mean()
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        term1 = ((rank(1 / data["close"]) * data["volume"]) / adv20)
        term2 = (data["high"] * rank(data["high"] - data["close"])) / (data["high"].rolling(5).mean() / 5)
        return (term1 * term2) - rank(vwap - delay(vwap, 5))
