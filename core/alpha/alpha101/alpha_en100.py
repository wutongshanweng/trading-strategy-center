"""Real WorldQuant Alpha101 formula — alpha100"""
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
class Alpha100_en(AlphaFactor):
    """alpha100: 0-(1*(((1.5*scale(((close-low)-(high-close))/(high-low)*volume)))-scale((correlation(close,rank(adv20),5)-rank(ts_argmin(close,30)))))*(volume/adv20))"""

    @property
    def name(self) -> str:
        return "alpha_en_100"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "0-(1*(((1.5*scale(((close-low)-(high-close))/(high-low)*volume)))-scale((correlation(close,rank(adv20),5)-rank(ts_argmin(close,30)))))*(volume/adv20))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv20 = ts_mean(data["volume"], 20)
        close_low = data["close"] - data["low"]
        high_close = data["high"] - data["close"]
        hl_range = data["high"] - data["low"] + 1e-9
        position = (close_low - high_close) / hl_range
        scale1 = scale(position * data["volume"])
        part1 = 1.5 * scale1
        rank_adv = rank(adv20)
        corr = correlation(data["close"], rank_adv, 5)
        argmin_close = ts_argmin(data["close"], 30)
        rank_argmin = rank(argmin_close)
        scale2 = scale(corr - rank_argmin)
        vol_ratio = data["volume"] / adv20
        return -1 * (part1 - scale2) * vol_ratio
