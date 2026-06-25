"""Real WorldQuant Alpha101 formula — Momentum alpha112: ((SUM(MAX(0, high - delay(close, 1)), 20) - SUM(MAX(0, delay(close, 1) - low), 20)) / (SUM(MAX(0, high - delay(close, 1)), 20) + SUM(MAX(0, delay(close, 1) - low), 20))) * 100"""
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
class Alpha112(AlphaFactor):
    """Momentum alpha112: ((SUM(MAX(0, high - delay(close, 1)), 20) - SUM(MAX(0, delay(close, 1) - low), 20)) / (SUM(MAX(0, high - delay(close, 1)), 20) + SUM(MAX(0, delay(close, 1) - low), 20))) * 100"""

    @property
    def name(self) -> str:
        return "alpha112"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha112: ((SUM(MAX(0, high - delay(close, 1)), 20) - SUM(MAX(0, delay(close, 1) - low), 20)) / (SUM(MAX(0, high - delay(close, 1)), 20) + SUM(MAX(0, delay(close, 1) - low), 20))) * 100"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        d_close = delay(data["close"], 1)
        up_move = ts_sum((data["high"] - d_close).clip(lower=0), 20)
        down_move = ts_sum((d_close - data["low"]).clip(lower=0), 20)
        return ((up_move - down_move) / (up_move + down_move + 1e-8)) * 100
