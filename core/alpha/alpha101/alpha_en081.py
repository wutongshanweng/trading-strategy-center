"""Real WorldQuant Alpha101 formula — alpha081"""
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
class Alpha081_en(AlphaFactor):
    """alpha081: (rank(log(product(rank((rank(correlation(vwap,sum(adv10,49.6),8.5))^4)),15)))<rank(correlation(rank(vwap),rank(volume),5.1)))*-1"""

    @property
    def name(self) -> str:
        return "alpha_en_081"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "(rank(log(product(rank((rank(correlation(vwap,sum(adv10,49.6),8.5))^4)),15)))<rank(correlation(rank(vwap),rank(volume),5.1)))*-1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv10 = ts_mean(data["volume"], 10)
        sum_adv = ts_sum(adv10, 50)
        corr = correlation(data["vwap"], sum_adv, 9)
        rank_corr = rank(rank(corr) ** 4)
        product_val = ts_product(rank_corr, 15)
        log_val = np.log(product_val + 1e-9)
        rank1 = rank(log_val)
        rank_vwap = rank(data["vwap"])
        rank_vol = rank(data["volume"])
        corr2 = correlation(rank_vwap, rank_vol, 5)
        rank2 = rank(corr2)
        cond = rank1 < rank2
        return pd.Series(np.where(cond, -1.0, 0.0), index=data.index)
