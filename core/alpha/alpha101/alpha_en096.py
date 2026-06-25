"""Real WorldQuant Alpha101 formula — alpha096"""
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
class Alpha096_en(AlphaFactor):
    """alpha096: (max(ts_rank(decay_linear(correlation(rank(vwap),rank(volume),3.8),4.2),8.4),ts_rank(decay_linear(ts_argmax(correlation(ts_rank(close,7.5),ts_rank(adv60,4.1),3.7),12.7),14),13.4))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_096"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "(max(ts_rank(decay_linear(correlation(rank(vwap),rank(volume),3.8),4.2),8.4),ts_rank(decay_linear(ts_argmax(correlation(ts_rank(close,7.5),ts_rank(adv60,4.1),3.7),12.7),14),13.4))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv60 = ts_mean(data["volume"], 60)
        rank_vwap = rank(data["vwap"])
        rank_vol = rank(data["volume"])
        corr1 = correlation(rank_vwap, rank_vol, 4)
        decay1 = decay_linear(corr1, 4)
        ts_rank1 = ts_rank(decay1, 8)
        ts_rank_close = ts_rank(data["close"], 8)
        ts_rank_adv = ts_rank(adv60, 4)
        corr2 = correlation(ts_rank_close, ts_rank_adv, 4)
        argmax_corr = ts_argmax(corr2, 13)
        decay2 = decay_linear(argmax_corr, 14)
        ts_rank2 = ts_rank(decay2, 13)
        combined = pd.concat([pd.Series(ts_rank1.values), pd.Series(ts_rank2.values)], axis=1).max(axis=1)
        return combined * -1
