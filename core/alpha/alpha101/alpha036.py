"""Real WorldQuant Alpha101 formula — Alpha036: (((((2.21 * rank(correlation((close - open), delay(volume, 1), 15))) + (0.7 * rank((open - close)))) + (0.73 * rank(Ts_Rank(delay((-1 * returns), 6), 5)))) + rank(abs(correlation(vwap, adv20, 6)))) + (0.6 * rank((((sma(close, 200) / 200) - open) * (close - open)))))"""
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
class Alpha036(AlphaFactor):
    """Alpha036: (((((2.21 * rank(correlation((close - open), delay(volume, 1), 15))) + (0.7 * rank((open - close)))) + (0.73 * rank(Ts_Rank(delay((-1 * returns), 6), 5)))) + rank(abs(correlation(vwap, adv20, 6)))) + (0.6 * rank((((sma(close, 200) / 200) - open) * (close - open)))))"""

    @property
    def name(self) -> str:
        return "alpha036"

    @property
    def category(self) -> str:
        return "complex_signal"

    @property
    def description(self) -> str:
        return "Alpha036: (((((2.21 * rank(correlation((close - open), delay(volume, 1), 15))) + (0.7 * rank((open - close)))) + (0.73 * rank(Ts_Rank(delay((-1 * returns), 6), 5)))) + rank(abs(correlation(vwap, adv20, 6)))) + (0.6 * rank((((sma(close, 200) / 200) - open) * (close - open)))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        ret = data["close"].pct_change()
        adv20 = data["volume"].rolling(20).mean()
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()

        term1 = 2.21 * rank(correlation(data["close"] - data["open"], delay(data["volume"], 1), 15))
        term2 = 0.7 * rank(data["open"] - data["close"])
        term3 = 0.73 * rank(ts_rank(delay(-1 * ret, 6), 5))
        term4 = rank(abs(correlation(vwap, adv20, 6)))
        w = min(200, len(data) - 1)
        term5 = 0.6 * rank((((data["close"].rolling(w).mean() / w) - data["open"]) * (data["close"] - data["open"])))
        return term1 + term2 + term3 + term4 + term5
