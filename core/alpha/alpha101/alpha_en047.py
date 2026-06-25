"""Real WorldQuant Alpha101 formula — alpha047"""
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
class Alpha047_en(AlphaFactor):
    """alpha047: ((((rank((1/close))*volume)/adv20)*((high*rank((high-close)))/(sum(high,5)/5)))-rank((vwap-delay(vwap,5))))"""

    @property
    def name(self) -> str:
        return "alpha_en_047"

    @property
    def category(self) -> str:
        return "complex"

    @property
    def description(self) -> str:
        return "((((rank((1/close))*volume)/adv20)*((high*rank((high-close)))/(sum(high,5)/5)))-rank((vwap-delay(vwap,5))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        adv20 = ts_mean(data["volume"], 20)
        rank1 = rank(1 / data["close"])
        vol_ratio = (rank1 * data["volume"]) / adv20
        rank_hc = rank(data["high"] - data["close"])
        avg_high_5 = ts_sum(data["high"], 5) / 5
        high_ratio = (data["high"] * rank_hc) / (avg_high_5 + 1e-9)
        vwap_diff = data["vwap"] - delay(data["vwap"], 5)
        rank_vwap = rank(vwap_diff)
        return vol_ratio * high_ratio - rank_vwap
