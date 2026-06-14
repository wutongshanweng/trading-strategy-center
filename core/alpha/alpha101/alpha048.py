"""Real WorldQuant Alpha101 formula — Alpha048: (indneutralize(((correlation(delta(close, 1), delta(delay(close, 1), 1), 250) * delta(close, 1)) / close), IndClass.subindustry) / sum(((delta(close, 1) / delay(close, 1))^2), 250))

Note: Requires industry neutralization data. Simplified implementation uses correlation-based momentum."""
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
class Alpha048(AlphaFactor):
    """Alpha048: Industry-neutralized momentum (simplified)"""

    @property
    def name(self) -> str:
        return "alpha048"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Alpha048: Industry-neutralized momentum (simplified)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        c = data["close"]
        w = min(250, len(data) - 1)
        autocorr = correlation(delta(c, 1), delta(delay(c, 1), 1), w)
        return rank(autocorr * delta(c, 1) / (c + 1e-8))
