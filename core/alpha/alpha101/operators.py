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


# ===== 国泰君安因子额外操作符 =====

def sma(x: pd.Series, d: int, e: int) -> pd.Series:
    """Exponential moving average (exponentially weighted moving average).

    Args:
        x: Input series
        d: Span/lookback period
        e: Not used in EMA, kept for compatibility
    """
    return x.ewm(span=d, adjust=False).mean()


def wma(x: pd.Series, d: int) -> pd.Series:
    """Weighted moving average - linear weighting."""
    weights = np.arange(1, d + 1, dtype=float)
    weights /= weights.sum()

    def _weighted(s):
        n = len(s)
        w = weights[-n:] if n < d else weights
        return np.dot(s, w) if len(s) > 0 else np.nan
    return x.rolling(d, min_periods=1).apply(_weighted, raw=True)


def sme(s: pd.Series, window: int, min_periods: int = 1) -> pd.Series:
    """Smoothed moving average."""
    return s.ewm(alpha=0.2, adjust=False).mean().rolling(window, min_periods=min_periods).mean()


def std(x: pd.Series, d: int) -> pd.Series:
    """Rolling standard deviation."""
    return x.rolling(d, min_periods=max(1, d // 2)).std()


def mean(x: pd.Series, d: int) -> pd.Series:
    """Rolling mean."""
    return x.rolling(d, min_periods=max(1, d // 2)).mean()


def vwap(data: pd.DataFrame, d: int = None) -> pd.Series:
    """Volume Weighted Average Price."""
    if d is None:
        return (data["close"] * data["volume"]).cumsum() / data["volume"].cumsum()
    return ((data["close"] * data["volume"]).rolling(d).sum() /
            data["volume"].rolling(d).sum())


def covi(x: pd.Series, y: pd.Series, d: int) -> pd.Series:
    """Rolling covariance (COVIANCE alias)."""
    return x.rolling(d, min_periods=max(1, d // 2)).cov(y)


def sequence(d: int) -> pd.Series:
    """Sequence of integers 1 to d."""
    return pd.Series(np.arange(1, d + 1))


def tsmin(x: pd.Series, d: int) -> pd.Series:
    """Time-series minimum alias."""
    return ts_min(x, d)


def tsmax(x: pd.Series, d: int) -> pd.Series:
    """Time-series maximum alias."""
    return ts_max(x, d)


def count(cond: pd.Series, d: int) -> pd.Series:
    """Count of True values in rolling window."""
    return cond.rolling(d, min_periods=max(1, d // 2)).sum()


def regbeta(y: pd.Series, x: pd.Series, d: int = None) -> pd.Series:
    """Rolling regression beta (slope).

    If x is a sequence, performs OLS. Otherwise uses rolling covariance.
    """
    if d is None:
        d = len(x) if isinstance(x, pd.Series) else 20
    if isinstance(x, pd.Series) and len(x) == d:
        # Fixed-window regression using sequence
        cov = y.rolling(d).cov(x)
        var = x.rolling(d).var()
        return cov / (var + 1e-8)
    return y.rolling(d).cov(x) / (x.rolling(d).var() + 1e-8)


def retr(data: pd.DataFrame) -> pd.Series:
    """Daily returns."""
    return data["close"].pct_change()


def tsr(x: pd.Series, d: int) -> pd.Series:
    """Time series rank alias for ts_rank."""
    return ts_rank(x, d)


def lowday(x: pd.Series, d: int) -> pd.Series:
    """Days since lowest value in window."""
    def _lowday(s):
        if len(s) == 0:
            return 0
        return len(s) - 1 - np.argmin(s[::-1])
    return x.rolling(d).apply(_lowday, raw=True)


def highday(x: pd.Series, d: int) -> pd.Series:
    """Days since highest value in window."""
    def _highday(s):
        if len(s) == 0:
            return 0
        return len(s) - 1 - np.argmax(s[::-1])
    return x.rolling(d).apply(_highday, raw=True)


def amount(data: pd.DataFrame) -> pd.Series:
    """Trading amount (money volume)."""
    if "amount" in data.columns:
        return data["amount"]
    return data["close"] * data["volume"]


def product(x: pd.Series, d: int) -> pd.Series:
    """Rolling product."""
    return ts_product(x, d)


def sign(x: pd.Series) -> pd.Series:
    """Sign of values."""
    return np.sign(x)


def sumif(cond: pd.Series, d: int, col: pd.Series) -> pd.Series:
    """Sum where condition is true in rolling window."""
    return cond.rolling(d).apply(lambda s: col.iloc[-len(s):][s > 0].sum() if s.sum() > 0 else 0, raw=False)


def _cond_sum(cond: pd.Series, val: pd.Series, d: int) -> pd.Series:
    """Conditional rolling sum."""
    return cond.rolling(d).apply(
        lambda s: val.iloc[-len(s):][s > 0].sum() if len(s) > 0 else 0,
        raw=False
    )


def tsargmax(x: pd.Series, d: int) -> pd.Series:
    """Time-series argmax alias."""
    return ts_argmax(x, d)


def tsargmin(x: pd.Series, d: int) -> pd.Series:
    """Time-series argmin alias."""
    return ts_argmin(x, d)


def cci(high: pd.Series, low: pd.Series, close: pd.Series, d: int) -> pd.Series:
    """Commodity Channel Index."""
    tp = (high + low + close) / 3
    sma = tp.rolling(d).mean()
    mad = tp.rolling(d).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    return (tp - sma) / (0.015 * mad + 1e-8)


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On Balance Volume."""
    return (np.sign(close.diff()) * volume).fillna(0).cumsum()


def tr(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """True Range."""
    h_diff = high - low
    h_close = (high - close.shift(1)).abs()
    l_close = (low - close.shift(1)).abs()
    return pd.concat([h_diff, h_close, l_close], axis=1).max(axis=1)


def ld_hd(high: pd.Series, low: pd.Series, close: pd.Series) -> tuple:
    """LD (plus) and HD (minus) for directional movement."""
    high_diff = high.diff()
    low_diff = -low.diff()
    plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
    minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
    return plus_dm, minus_dm


def sumac(x: pd.Series) -> pd.Series:
    """Sum accumulation (cumulative sum)."""
    return x.cumsum()


def abs(x: pd.Series) -> pd.Series:
    """Absolute value."""
    return np.abs(x)


def log(x: pd.Series) -> pd.Series:
    """Natural logarithm."""
    return np.log(x.clip(lower=1e-8))


def min(a: pd.Series, b: pd.Series) -> pd.Series:
    """Element-wise minimum."""
    return np.minimum(a, b)


def max(a: pd.Series, b: pd.Series) -> pd.Series:
    """Element-wise maximum."""
    return np.maximum(a, b)


def if_else(cond: pd.Series, then: float, else_: float) -> pd.Series:
    """Conditional replacement."""
    return cond.where(cond > 0, else_).where(cond <= 0, then)
