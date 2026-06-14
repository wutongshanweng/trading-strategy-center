"""IV Rank / IV Percentile / 波动率锥 — 期权择时核心指标。"""
from __future__ import annotations

import numpy as np
import pandas as pd


def iv_rank(iv_series: pd.Series, lookback: int = 252) -> float:
    """IV Rank = (当前IV - 区间最低) / (区间最高 - 区间最低)，范围 0~100。

    衡量当前隐含波动率在过去 lookback 个交易日的相对高低位。
    高 IV Rank -> 倾向卖波动率；低 IV Rank -> 倾向买波动率。
    """
    s = iv_series.dropna().tail(lookback)
    if len(s) < 2:
        return float("nan")
    lo, hi = s.min(), s.max()
    if hi - lo < 1e-12:
        return 50.0
    return float((s.iloc[-1] - lo) / (hi - lo) * 100.0)


def iv_percentile(iv_series: pd.Series, lookback: int = 252) -> float:
    """IV Percentile = 过去 lookback 天中 IV 低于当前值的天数占比，范围 0~100。"""
    s = iv_series.dropna().tail(lookback)
    if len(s) < 2:
        return float("nan")
    current = s.iloc[-1]
    return float((s < current).mean() * 100.0)


def vol_cone(rv_series: pd.Series, windows=(5, 10, 20, 30, 60, 90),
             quantiles=(0.10, 0.25, 0.50, 0.75, 0.90)) -> pd.DataFrame:
    """波动率锥：不同观察窗口下 RV 的分位数分布。

    返回 DataFrame，行=window，列=分位数 + current。
    """
    close = rv_series.dropna()
    log_ret = np.log(close / close.shift(1)).dropna()
    rows = {}
    for w in windows:
        rolling_rv = log_ret.rolling(w).std(ddof=0) * np.sqrt(252)
        rolling_rv = rolling_rv.dropna()
        if rolling_rv.empty:
            continue
        row = {f"q{int(q*100)}": float(rolling_rv.quantile(q)) for q in quantiles}
        row["current"] = float(rolling_rv.iloc[-1])
        rows[w] = row
    return pd.DataFrame.from_dict(rows, orient="index")
