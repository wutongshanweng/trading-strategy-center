"""Real WorldQuant Alpha101 formula — Alpha039: ((-1 * rank((delta(close, 7) * (1 - rank(decay_linear((volume / adv20), 9)))))) * (1 + rank(sma(returns, 250))))"""
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
class Alpha039(AlphaFactor):
    """Alpha039: ((-1 * rank((delta(close, 7) * (1 - rank(decay_linear((volume / adv20), 9)))))) * (1 + rank(sma(returns, 250))))"""

    @property
    def name(self) -> str:
        return "alpha039"

    @property
    def category(self) -> str:
        return "volume_price"

    @property
    def description(self) -> str:
        return "Alpha039: ((-1 * rank((delta(close, 7) * (1 - rank(decay_linear((volume / adv20), 9)))))) * (1 + rank(sma(returns, 250))))"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        ret = data["close"].pct_change()
        adv20 = data["volume"].rolling(20).mean()
        dl = decay_linear((data["volume"] / adv20).to_frame(), 9).iloc[:, 0]
        inner = delta(data["close"], 7) * (1 - rank(dl))
        w = min(250, len(data) - 1)
        return (-1 * rank(inner)) * (1 + rank(data["close"].pct_change().rolling(w).mean()))
