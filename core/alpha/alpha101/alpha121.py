"""Real WorldQuant Alpha101 formula — Momentum alpha121: (rank((vwap - min(vwap, 12))) ** ts_rank(correlation(ts_rank(vwap, 20), ts_rank(mean(volume, 60), 2), 18), 3)) * -1"""
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
class Alpha121(AlphaFactor):
    """Momentum alpha121: (rank((vwap - min(vwap, 12))) ** ts_rank(correlation(ts_rank(vwap, 20), ts_rank(mean(volume, 60), 2), 18), 3)) * -1"""

    @property
    def name(self) -> str:
        return "alpha121"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha121: (rank((vwap - min(vwap, 12))) ** ts_rank(correlation(ts_rank(vwap, 20), ts_rank(mean(volume, 60), 2), 18), 3)) * -1"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Calculate vwap if not available
        if "vwap" in data.columns:
            vwap = data["vwap"]
        else:
            vwap = (data["high"] + data["low"] + data["close"]) / 3

        rank_diff = rank(vwap - ts_min(vwap, 12))
        ts_rank_vwap = ts_rank(vwap, 20)
        ts_rank_vol = ts_rank(ts_mean(data["volume"], 60), 2)
        corr = correlation(ts_rank_vwap, ts_rank_vol, 18)
        ts_rank_corr = ts_rank(corr, 3)
        return (rank_diff ** ts_rank_corr) * -1
