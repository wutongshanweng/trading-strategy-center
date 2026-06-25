"""Real WorldQuant Alpha101 formula — alpha036"""
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
class Alpha036_en(AlphaFactor):
    """alpha036: ((((2.21*rank(correlation((close-open),delay(volume,1),15)))+(0.7*rank((open-close))))+(0.73*rank(ts_rank(delay((-1*returns),6),5))))+rank(abs(correlation(vwap,adv20,6))))+(0.6*rank((((sum(close,200)/200)-open)*(close-open)))))"""

    @property
    def name(self) -> str:
        return "alpha_en_036"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "((((2.21*rank(correlation((close-open),delay(volume,1),15)))+(0.7*rank((open-close))))+(0.73*rank(ts_rank(delay((-1*returns),6),5))))+rank(abs(correlation(vwap,adv20,6))))+(0.6*rank((((sum(close,200)/200)-open)*(close-open)))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        returns = data["close"].pct_change()
        adv20 = ts_mean(data["volume"], 20)
        close_open_diff = data["close"] - data["open"]
        delayed_vol = delay(data["volume"], 1)
        corr1 = correlation(close_open_diff, delayed_vol, 15)
        part1 = 2.21 * rank(corr1)
        part2 = 0.7 * rank(data["open"] - data["close"])
        delayed_ret = delay(-1 * returns, 6)
        ts_rank_ret = ts_rank(delayed_ret, 5)
        part3 = 0.73 * rank(ts_rank_ret)
        corr2 = abs(correlation(data["vwap"], adv20, 6))
        part4 = rank(corr2)
        avg_close_200 = ts_sum(data["close"], 200) / 200
        part5 = 0.6 * rank((avg_close_200 - data["open"]) * (data["close"] - data["open"]))
        return part1 + part2 + part3 + part4 + part5
