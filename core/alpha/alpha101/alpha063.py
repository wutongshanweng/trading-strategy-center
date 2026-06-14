"""Real WorldQuant Alpha101 formula — Alpha063: ((rank(decay_linear(delta(IndNeutralize(close, IndClass.industry), 2.25164), 8.22237)) - rank(decay_linear(correlation(((vwap * 0.318108) + (open * (1 - 0.318108))), sum(adv180, 37.2467), 13.557), 12.2883))) * -1)
Note: Requires industry neutralization. Simplified implementation."""
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
class Alpha063(AlphaFactor):
    """Alpha063: Industry-neutral momentum correlation (simplified)"""

    @property
    def name(self) -> str:
        return "alpha063"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha063: Industry-neutral momentum correlation (simplified)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        vwap = (data["close"] * data["volume"]).rolling(10).sum() / data["volume"].rolling(10).sum()
        dl1 = decay_linear(delta(data["close"], 2).to_frame(), 8).iloc[:, 0]
        blended = vwap * 0.318108 + data["open"] * 0.681892
        adv180 = data["volume"].rolling(180, min_periods=20).mean()
        corr = correlation(blended, adv180, 14)
        dl2 = decay_linear(corr.to_frame(), 12).iloc[:, 0]
        return (rank(dl1) - rank(dl2)) * -1
