"""Real WorldQuant Alpha101 formula — Alpha059: (-1 * Ts_Rank(decay_linear(correlation(IndNeutralize(((vwap * 0.728317) + (vwap * (1 - 0.728317))), IndClass.industry), volume, 4.25197), 16.2289), 8.19648))
Note: Requires industry neutralization data. Simplified implementation."""
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
class Alpha059(AlphaFactor):
    """Alpha059: Industry-neutral volume-price correlation (simplified)"""

    @property
    def name(self) -> str:
        return "alpha059"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha059: Industry-neutral volume-price correlation (simplified)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        corr = correlation(vwap * 0.728317 + vwap * 0.271683, data["volume"], 4)
        dl = decay_linear(corr.to_frame(), 16).iloc[:, 0]
        return -1 * ts_rank(dl, 8)
