"""Real WorldQuant Alpha101 formula — Momentum alpha172: mean(ABS(SUM(ld > 0 ? ld : 0, 14) * 100 / SUM(tr, 14) - SUM(hd > 0 ? hd : 0, 14) * 100 / SUM(tr, 14)) / ..., 6) — simplified KDJ-like"""
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
class Alpha172(AlphaFactor):
    """Momentum alpha172: mean(ABS(SUM(ld > 0 ? ld : 0, 14) * 100 / SUM(tr, 14) - SUM(hd > 0 ? hd : 0, 14) * 100 / SUM(tr, 14)) / ..., 6) — simplified KDJ-like"""

    @property
    def name(self) -> str:
        return "alpha172"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha172: mean(ABS(SUM(ld > 0 ? ld : 0, 14) * 100 / SUM(tr, 14) - SUM(hd > 0 ? hd : 0, 14) * 100 / SUM(tr, 14)) / ..., 6) — simplified KDJ-like"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        # Calculate true range
        tr1 = data["high"] - data["low"]
        tr2 = np.abs(data["high"] - delay(data["close"], 1))
        tr3 = np.abs(data["low"] - delay(data["close"], 1))
        tr = np.maximum(np.maximum(tr1, tr2), tr3)

        # Calculate stochastic-like values
        d_close = delay(data["close"], 1)
        ld = data["low"] - d_close
        hd = d_close - data["high"]

        ld_pos = ld.where(ld > 0, 0)
        hd_pos = hd.where(hd > 0, 0)

        sv = ts_sum(ld_pos, 14) * 100 / (ts_sum(tr, 14) + 1e-8)
        bv = ts_sum(hd_pos, 14) * 100 / (ts_sum(tr, 14) + 1e-8)
        abs_diff = np.abs(sv - bv)
        return ts_mean(abs_diff, 6)
