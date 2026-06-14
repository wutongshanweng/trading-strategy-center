"""Real WorldQuant Alpha101 formula — Alpha074: (-1 * (rank(correlation(close, sma(adv30, 37), 15)) < rank(correlation(rank((high * 0.0261661) + (vwap * (1 - 0.0261661))), rank(volume), 11))))"""
import numpy as np
import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .operators import (
    rank, ts_rank, ts_argmax, ts_argmin, ts_sum, ts_product,
    ts_min, ts_max, ts_mean, ts_std, ts_cov, correlation, covariance,
    scale, delay, delta, signedpower, decay_linear, signed_sqrt, bool_to_float,
)


@FactorRegistry.register
class Alpha074(AlphaFactor):
    """Alpha074: (-1 * (rank(correlation(close, sma(adv30, 37), 15)) < rank(correlation(rank((high * 0.0261661) + (vwap * (1 - 0.0261661))), rank(volume), 11))))"""

    @property
    def name(self) -> str:
        return "alpha074"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha074: (-1 * (rank(correlation(close, sma(adv30, 37), 15)) < rank(correlation(rank((high * 0.0261661) + (vwap * (1 - 0.0261661))), rank(volume), 11))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        adv30 = data["volume"].rolling(30).mean()
        corr1 = correlation(data["close"], adv30.rolling(37).mean(), 15)
        blended = data["high"] * 0.0261661 + vwap * 0.9738339
        corr2 = correlation(rank(blended), rank(data["volume"]), 11)
        cond = rank(corr1) < rank(corr2)
        return bool_to_float(cond, corr1, corr2, sign=-1.0)
