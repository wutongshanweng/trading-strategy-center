import numpy as np
import pandas as pd


def detect_engulfing(df: pd.DataFrame) -> pd.Series:
    bull = (df["close"] > df["open"]) & (df["open"].shift(1) > df["close"].shift(1))
    bull = bull & (df["close"] > df["open"].shift(1)) & (df["open"] < df["close"].shift(1))
    bear = (df["close"] < df["open"]) & (df["open"].shift(1) < df["close"].shift(1))
    bear = bear & (df["close"] < df["open"].shift(1)) & (df["open"] > df["close"].shift(1))
    return pd.Series(np.select([bull, bear], [1, -1], 0), index=df.index)


def detect_doji(df: pd.DataFrame, body_pct: float = 0.05) -> pd.Series:
    body = abs(df["close"] - df["open"])
    range_ = df["high"] - df["low"]
    return ((body / range_) < body_pct).astype(int)


def detect_hammer(df: pd.DataFrame, ratio: float = 0.3) -> pd.Series:
    body = abs(df["close"] - df["open"])
    lower = df[["open", "close"]].min(axis=1) - df["low"]
    upper = df["high"] - df[["open", "close"]].max(axis=1)
    return ((lower > body * 2) & (upper < body * ratio) & (body > 0)).astype(int)


def detect_shooting_star(df: pd.DataFrame, ratio: float = 0.3) -> pd.Series:
    body = abs(df["close"] - df["open"])
    lower = df[["open", "close"]].min(axis=1) - df["low"]
    upper = df["high"] - df[["open", "close"]].max(axis=1)
    return ((upper > body * 2) & (lower < body * ratio) & (body > 0)).astype(int)


def detect_inside_bar(df: pd.DataFrame) -> pd.Series:
    inside = (df["high"] < df["high"].shift(1)) & (df["low"] > df["low"].shift(1))
    return inside.astype(int)


def pivot_high(series: pd.Series, left: int = 3, right: int = 3) -> pd.Series:
    peaks = series.copy()
    for i in range(left, len(series) - right):
        window = series.iloc[i - left:i + right + 1]
        if series.iloc[i] != window.max():
            peaks.iloc[i] = np.nan
    return peaks


def pivot_low(series: pd.Series, left: int = 3, right: int = 3) -> pd.Series:
    troughs = series.copy()
    for i in range(left, len(series) - right):
        window = series.iloc[i - left:i + right + 1]
        if series.iloc[i] != window.min():
            troughs.iloc[i] = np.nan
    return troughs
