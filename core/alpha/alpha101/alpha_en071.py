"""Real WorldQuant Alpha101 formula — alpha071"""
import numpy as np
import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .operators import rank, ts_rank, ts_mean, correlation, decay_linear


@FactorRegistry.register
class Alpha071_en(AlphaFactor):
    """alpha071: max(ts_rank(decay_linear(correlation(ts_rank(close,3.4),ts_rank(adv180,12),18),4.2),15.7),ts_rank(decay_linear((rank(((low+open)-(vwap+vwap))))**2,16.5),4.4))"""

    @property
    def name(self) -> str:
        return "alpha_en_071"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "max(ts_rank(decay_linear(correlation(ts_rank(close,3.4),ts_rank(adv180,12),18),4.2),15.7),ts_rank(decay_linear((rank(((low+open)-(vwap+vwap))))**2,16.5),4.4))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv180 = ts_mean(data["volume"], 180)
        ts_rank_close = ts_rank(data["close"], 3)
        ts_rank_adv = ts_rank(adv180, 12)
        corr = correlation(ts_rank_close, ts_rank_adv, 18)
        decay1 = decay_linear(corr, 4)
        ts_rank1 = ts_rank(decay1, 16)
        inner = rank((data["low"] + data["open"]) - (data["vwap"] + data["vwap"]))
        decay2 = decay_linear(inner ** 2, 17)
        ts_rank2 = ts_rank(decay2, 4)
        return pd.concat([ts_rank1, ts_rank2], axis=1).max(axis=1)
