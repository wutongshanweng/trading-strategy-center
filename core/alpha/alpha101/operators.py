"""WorldQuant Alpha101 operators — building blocks for complex factor expressions."""

from __future__ import annotations

import numpy as np
import pandas as pd


def rank(x: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """Cross-sectional rank (percentile)."""
    return x.rank(pct=True)


def ts_rank(x: pd.Series, d: int = 5) -> pd.Series:
    """Time-series rank over d-day window."""
    return x.rolling(d, min_periods=max(1, d // 2)).apply(
        lambda s: pd.Series(s).rank(pct=True).iloc[-1] if len(s) > 0 else 0.5,
        raw=False,
    )


def ts_argmax(x: pd.Series, d: int = 5) -> pd.Series:
    """Time-series argmax — which day had the max value."""
    return x.rolling(d, min_periods=max(1, d // 2)).apply(
        lambda s: np.argmax(s) if len(s) > 0 else 0, raw=True
    )


def ts_argmin(x: pd.Series, d: int = 5) -> pd.Series:
    """Time-series argmin — which day had the min value."""
    return x.rolling(d, min_periods=max(1, d // 2)).apply(
        lambda s: np.argmin(s) if len(s) > 0 else 0, raw=True
    )


def _minp(d: int) -> int:
    """Return minimum periods for rolling: requires full window to produce NaN on prefix."""
    return max(d // 2, 1)


def ts_sum(x: pd.Series, d: int = 5) -> pd.Series:
    return x.rolling(d, min_periods=_minp(d)).sum()


def ts_product(x: pd.Series, d: int = 5) -> pd.Series:
    return x.rolling(d, min_periods=_minp(d)).apply(
        lambda s: np.prod(s) if len(s) > 0 else 0, raw=True
    )


def ts_min(x: pd.Series, d: int = 5) -> pd.Series:
    return x.rolling(d, min_periods=_minp(d)).min()


def ts_max(x: pd.Series, d: int = 5) -> pd.Series:
    return x.rolling(d, min_periods=_minp(d)).max()


def ts_mean(x: pd.Series, d: int = 5) -> pd.Series:
    return x.rolling(d, min_periods=_minp(d)).mean()


def ts_std(x: pd.Series, d: int = 5) -> pd.Series:
    return x.rolling(d, min_periods=_minp(d)).std()


def ts_cov(x: pd.Series, y: pd.Series, d: int = 5) -> pd.Series:
    return x.rolling(d, min_periods=_minp(d)).cov(y)


def correlation(x: pd.Series, y: pd.Series, d: int = 5) -> pd.Series:
    return x.rolling(d, min_periods=_minp(d)).corr(y)


def covariance(x: pd.Series, y: pd.Series, d: int = 5) -> pd.Series:
    return x.rolling(d, min_periods=_minp(d)).cov(y)


def scale(x: pd.Series) -> pd.Series:
    """Z-score normalize to sum of absolute values = 1."""
    a = x.abs().sum()
    return x / a if a != 0 else x


def delay(x: pd.Series, d: int = 1) -> pd.Series:
    return x.shift(d)


def delta(x: pd.Series, d: int = 1) -> pd.Series:
    return x - x.shift(d)


def signedpower(x: pd.Series, e: float = 2.0) -> pd.Series:
    return np.sign(x) * np.abs(x) ** e


def decay_linear(x: pd.Series, d: int = 5) -> pd.Series:
    """Linearly weighted moving average — most recent has highest weight."""
    weights = np.arange(1, d + 1, dtype=float)
    weights /= weights.sum()

    def _weighted(s):
        return np.dot(s, weights[: len(s)]) if len(s) > 0 else 0

    return x.rolling(d, min_periods=1).apply(_weighted, raw=True)


def ts_rank_decay_linear(x: pd.Series, d: int = 5) -> pd.Series:
    """ts_rank of decay_linear."""
    return ts_rank(decay_linear(x, d), d)


def highlow_ratio(x: pd.Series, y: pd.Series) -> pd.Series:
    """(x - y) / ((x + y) / 2) — mid-point normalized range."""
    return (x - y) / ((x + y) / 2 + 1e-8)


def signed_sqrt(x: pd.Series) -> pd.Series:
    """Signed square root."""
    return np.sign(x) * np.sqrt(np.abs(x))


def bool_to_float(cond: pd.Series, *inputs: pd.Series, sign: float = 1.0) -> pd.Series:
    """Convert a boolean condition to float while preserving NaN warmup.

    A naive ``cond.astype(float)`` turns ``NaN < NaN`` (undefined during the
    rolling warmup period) into ``0.0``, which hides the fact that the factor
    is not yet computable. This helper re-applies NaN to any bar where one of
    the underlying ranked/rolling inputs is NaN, so warmup bars stay undefined.

    Args:
        cond: Boolean Series from a comparison expression.
        *inputs: The Series that fed the comparison; bars where any is NaN
            become NaN in the result.
        sign: Multiplier applied to the float result (e.g. -1.0).
    """
    res = cond.astype(float) * sign
    if inputs:
        mask = inputs[0].isna()
        for inp in inputs[1:]:
            mask = mask | inp.isna()
        res[mask] = np.nan
    return res
