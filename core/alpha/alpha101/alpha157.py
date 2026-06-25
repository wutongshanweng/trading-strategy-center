"""Real WorldQuant Alpha101 formula — Momentum alpha157: MIN(product(rank(rank(log(sum(tsmin(rank(rank((-1 * rank(delta((close - 1), 5)))), 2), 1)))), 1), 5) + ts_rank(delay((-1 * returns), 6), 5)"""
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
class Alpha157(AlphaFactor):
    """Momentum alpha157: MIN(product(rank(rank(log(sum(tsmin(rank(rank((-1 * rank(delta((close - 1), 5)))), 2), 1)))), 1), 5) + ts_rank(delay((-1 * returns), 6), 5)"""

    @property
    def name(self) -> str:
        return "alpha157"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum alpha157: MIN(product(rank(rank(log(sum(tsmin(rank(rank((-1 * rank(delta((close - 1), 5)))), 2), 1)))), 1), 5) + ts_rank(delay((-1 * returns), 6), 5)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        returns = data["close"].pct_change()

        # Complex nested ranking
        delta_close = delta(data["close"] - 1, 5)
        rank1 = rank(-1 * rank(delta_close))
        ts_min_rank = ts_min(rank1, 2)
        sum_ts_min = ts_sum(ts_min_rank, 1)
        log_sum = np.log(sum_ts_min.clip(lower=1e-8))
        rank_log = rank(rank(log_sum))
        product_rank = ts_product(rank_log, 5)

        # Second term
        delayed_ret = delay(-1 * returns, 6)
        ts_rank_ret = ts_rank(delayed_ret, 5)

        return np.minimum(product_rank, ts_rank_ret) + ts_rank_ret
