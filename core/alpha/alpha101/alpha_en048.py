"""Real WorldQuant Alpha101 formula — alpha048"""
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
class Alpha048_en(AlphaFactor):
    """alpha048: ((correlation(delta(close,1),delta(delay(close,1),1),250)*delta(close,1))/close) / sum(((delta(close,1)/delay(close,1))**2),250)"""

    @property
    def name(self) -> str:
        return "alpha_en_048"

    @property
    def category(self) -> str:
        return "volatility"

    @property
    def description(self) -> str:
        return "((correlation(delta(close,1),delta(delay(close,1),1),250)*delta(close,1))/close) / sum(((delta(close,1)/delay(close,1))**2),250)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        delta_close_1 = delta(data["close"], 1)
        delayed_delta = delta(delay(data["close"], 1), 1)
        corr = correlation(delta_close_1, delayed_delta, 250)
        numerator = (corr * delta_close_1) / (data["close"] + 1e-9)
        ret_ratio = delta_close_1 / (delay(data["close"], 1) + 1e-9)
        denominator = ts_sum(ret_ratio ** 2, 250)
        return numerator / (denominator + 1e-9)
