"""Real WorldQuant Alpha101 formula — Momentum alpha170: (((rank((1 / close)) * volume / mean(volume, 20)) * ((high * rank(high - close)) / (sum(high, 5) / 5))) - rank((vwap - delay(vwap, 5))))"""
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
class Alpha170(AlphaFactor):
    """Momentum alpha170: (((rank((1 / close)) * volume / mean(volume, 20)) * ((high * rank(high - close)) / (sum(high, 5) / 5))) - rank((vwap - delay(vwap, 5))))"""

    @property
    def name(self) -> str:
        return "alpha170"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha170: (((rank((1 / close)) * volume / mean(volume, 20)) * ((high * rank(high - close)) / (sum(high, 5) / 5))) - rank((vwap - delay(vwap, 5))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Calculate vwap if not available
        if "vwap" in data.columns:
            vwap = data["vwap"]
        else:
            vwap = (data["high"] + data["low"] + data["close"]) / 3

        # First term
        rank_inv_close = rank(1 / (data["close"] + 1e-8))
        vol_ratio = data["volume"] / (ts_mean(data["volume"], 20) + 1e-8)
        rank_hl = rank(data["high"] - data["close"])
        sum_high_5 = ts_sum(data["high"], 5) / 5
        term1 = rank_inv_close * vol_ratio * (data["high"] * rank_hl / (sum_high_5 + 1e-8))

        # Second term
        rank_vwap_diff = rank(vwap - delay(vwap, 5))

        return term1 - rank_vwap_diff
