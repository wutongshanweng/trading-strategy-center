import numpy as np
import pandas as pd


def SMA(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period).mean()


def EMA(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def RSI(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def MACD(series: pd.Series, fast=12, slow=26, signal=9):
    ema_fast = EMA(series, fast)
    ema_slow = EMA(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = EMA(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def ATR(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def BB(series: pd.Series, period: int = 20, std_dev: float = 2.0):
    mid = SMA(series, period)
    std = series.rolling(period).std()
    upper = mid + std_dev * std
    lower = mid - std_dev * std
    return upper, mid, lower


def KDJ(df: pd.DataFrame, period: int = 9, k_smooth: int = 3, d_smooth: int = 3):
    low_min = df["low"].rolling(period).min()
    high_max = df["high"].rolling(period).max()
    rsv = (df["close"] - low_min) / (high_max - low_min + 1e-10) * 100
    k = rsv.ewm(alpha=1/k_smooth, adjust=False).mean()
    d = k.ewm(alpha=1/d_smooth, adjust=False).mean()
    j = 3 * k - 2 * d
    return k, d, j


def AROON(df: pd.DataFrame, period: int = 14):
    up = 100 * df["high"].rolling(period + 1).apply(lambda x: x.argmax()) / period
    down = 100 * df["low"].rolling(period + 1).apply(lambda x: x.argmin()) / period
    return up, down


def CCI(df: pd.DataFrame, period: int = 20):
    tp = (df["high"] + df["low"] + df["close"]) / 3
    sma = tp.rolling(period).mean()
    mad = tp.rolling(period).apply(lambda x: np.mean(np.abs(x - x.mean())))
    return (tp - sma) / (0.015 * mad + 1e-10)


def OBV(df: pd.DataFrame) -> pd.Series:
    obv = (df["volume"] * np.sign(df["close"].diff())).fillna(0).cumsum()
    return obv


def VWAP(df: pd.DataFrame) -> pd.Series:
    return (df["close"] * df["volume"]).cumsum() / df["volume"].cumsum()


def DONCHIAN(df: pd.DataFrame, period: int = 20):
    upper = df["high"].rolling(period).max()
    lower = df["low"].rolling(period).min()
    mid = (upper + lower) / 2
    return upper, mid, lower


def ADX(df: pd.DataFrame, period: int = 14):
    high, low, close = df["high"], df["low"], df["close"]
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    up_move = high - high.shift()
    down_move = low.shift() - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    atr = tr.rolling(period).mean()
    pdi = 100 * pd.Series(plus_dm).rolling(period).sum() / (atr + 1e-10)
    ndi = 100 * pd.Series(minus_dm).rolling(period).sum() / (atr + 1e-10)
    dx = 100 * (pdi - ndi).abs() / (pdi + ndi + 1e-10)
    adx = dx.rolling(period).mean()
    return adx, pdi, ndi


def SUPERTREND(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0):
    high, low, close = df["high"], df["low"], df["close"]
    hl2 = (high + low) / 2
    atr = ATR(df, period)
    upper = hl2 + multiplier * atr
    lower = hl2 - multiplier * atr

    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=float)

    supertrend.iloc[0] = upper.iloc[0]
    direction.iloc[0] = 1

    for i in range(1, len(df)):
        if close.iloc[i] > upper.iloc[i - 1]:
            direction.iloc[i] = 1
        elif close.iloc[i] < lower.iloc[i - 1]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i - 1]

        if direction.iloc[i] == 1:
            supertrend.iloc[i] = lower.iloc[i]
        else:
            supertrend.iloc[i] = upper.iloc[i]

    return supertrend, direction


def WILLIAMS_R(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_max = df["high"].rolling(period).max()
    low_min = df["low"].rolling(period).min()
    wr = -100 * (high_max - df["close"]) / (high_max - low_min + 1e-10)
    return wr


def MFI(df: pd.DataFrame, period: int = 14) -> pd.Series:
    tp = (df["high"] + df["low"] + df["close"]) / 3
    money_flow = tp * df["volume"]
    positive_flow = pd.Series(0.0, index=df.index)
    negative_flow = pd.Series(0.0, index=df.index)

    tp_diff = tp.diff()
    positive_flow[tp_diff > 0] = money_flow[tp_diff > 0]
    negative_flow[tp_diff < 0] = money_flow[tp_diff < 0]

    pos_sum = positive_flow.rolling(period).sum()
    neg_sum = negative_flow.rolling(period).sum()
    mfi = 100 - 100 / (1 + pos_sum / (neg_sum + 1e-10))
    return mfi


def TRIX(series: pd.Series, period: int = 15) -> pd.Series:
    ema1 = EMA(series, period)
    ema2 = EMA(ema1, period)
    ema3 = EMA(ema2, period)
    return ema3.pct_change() * 100


def AROON_OSCILLATOR(df: pd.DataFrame, period: int = 14) -> pd.Series:
    up, down = AROON(df, period)
    return up - down
