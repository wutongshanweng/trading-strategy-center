"""Real WorldQuant Alpha101 formula — Momentum alpha154: (vwap - min(vwap, 16)) < correlation(vwap, mean(volume, 180), 18) — output 1 or 0, then scale"""
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
class Alpha154(AlphaFactor):
    """Momentum alpha154: (vwap - min(vwap, 16)) < correlation(vwap, mean(volume, 180), 18) — output 1 or 0, then scale"""

    @property
    def name(self) -> str:
        return "alpha154"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha154: (vwap - min(vwap, 16)) < correlation(vwap, mean(volume, 180), 18) — output 1 or 0, then scale"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Calculate vwap if not available
        if "vwap" in data.columns:
            vwap = data["vwap"]
        else:
            vwap = (data["high"] + data["low"] + data["close"]) / 3

        vwap_diff = vwap - ts_min(vwap, 16)
        corr = correlation(vwap, ts_mean(data["volume"], 180), 18)
        result = (vwap_diff < corr).astype(float)
        return scale(result)
