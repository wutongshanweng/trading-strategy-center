"""Real WorldQuant Alpha101 formula — Momentum alpha114: rank((high - low) / SUM(close, 5) * 5) * rank(volume) / ((high - low) / SUM(close, 5) * 5 / (vwap - close))"""
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
class Alpha114(AlphaFactor):
    """Momentum alpha114: rank((high - low) / SUM(close, 5) * 5) * rank(volume) / ((high - low) / SUM(close, 5) * 5 / (vwap - close))"""

    @property
    def name(self) -> str:
        return "alpha114"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha114: rank((high - low) / SUM(close, 5) * 5) * rank(volume) / ((high - low) / SUM(close, 5) * 5 / (vwap - close))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Calculate vwap if not available
        if "vwap" in data.columns:
            vwap = data["vwap"]
        else:
            vwap = (data["high"] + data["low"] + data["close"]) / 3

        hl = data["high"] - data["low"]
        sum_close_5 = ts_sum(data["close"], 5)
        hl_normalized = hl / sum_close_5 * 5
        rank_hl = rank(hl_normalized)
        rank_vol = rank(data["volume"])
        vwap_diff = vwap - data["close"]
        return rank_hl * rank_vol / (hl_normalized / (vwap_diff + 1e-8))
