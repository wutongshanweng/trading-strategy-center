"""Real WorldQuant Alpha101 formula — Alpha058: (-1 * Ts_Rank(decay_linear(correlation(IndNeutralize(vwap, IndClass.sector), volume, 3.92795), 7.89291), 5.50322))
Note: Requires sector neutralization data. Simplified implementation uses direct correlation."""
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
class Alpha058(AlphaFactor):
    """Alpha058: Sector-neutral volume-price correlation (simplified)"""

    @property
    def name(self) -> str:
        return "alpha058"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha058: Sector-neutral volume-price correlation (simplified)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        corr = correlation(vwap, data["volume"], 4)
        dl = decay_linear(corr.to_frame(), 8).iloc[:, 0]
        return -1 * ts_rank(dl, 5)
