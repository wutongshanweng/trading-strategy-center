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


# ============================================================
# 扩展指标库(供新策略使用)
# ============================================================

def STDDEV(series: pd.Series, period: int = 20) -> pd.Series:
    """滚动标准差。"""
    return series.rolling(period).std(ddof=0)


def ZSCORE(series: pd.Series, period: int = 20) -> pd.Series:
    """滚动 Z-score = (x - 均值) / 标准差。"""
    mean = series.rolling(period).mean()
    std = series.rolling(period).std(ddof=0)
    return (series - mean) / std.replace(0, np.nan)


def ROC(series: pd.Series, period: int = 12) -> pd.Series:
    """Rate of Change(变动率,%)。"""
    return (series / series.shift(period) - 1) * 100


def KAMA(series: pd.Series, period: int = 10, fast: int = 2, slow: int = 30) -> pd.Series:
    """Kaufman 自适应均线 (KAMA)。"""
    change = (series - series.shift(period)).abs()
    volatility = series.diff().abs().rolling(period).sum()
    er = (change / volatility.replace(0, np.nan)).fillna(0)
    fast_sc = 2 / (fast + 1)
    slow_sc = 2 / (slow + 1)
    sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
    kama = pd.Series(index=series.index, dtype=float)
    first_valid = series.first_valid_index()
    if first_valid is None:
        return kama
    start = series.index.get_loc(first_valid)
    kama.iloc[start] = series.iloc[start]
    for i in range(start + 1, len(series)):
        prev = kama.iloc[i - 1]
        if pd.isna(prev):
            kama.iloc[i] = series.iloc[i]
        else:
            kama.iloc[i] = prev + sc.iloc[i] * (series.iloc[i] - prev)
    return kama


def KELTNER(df: pd.DataFrame, period: int = 20, mult: float = 2.0):
    """Keltner 通道(EMA ± mult*ATR)。返回 (upper, mid, lower)。"""
    mid = EMA(df["close"], period)
    atr = ATR(df, period)
    upper = mid + mult * atr
    lower = mid - mult * atr
    return upper, mid, lower


def PARABOLIC_SAR(df: pd.DataFrame, af_step: float = 0.02, af_max: float = 0.2) -> pd.Series:
    """抛物线 SAR。"""
    high, low = df["high"].values, df["low"].values
    n = len(df)
    sar = np.zeros(n)
    if n < 2:
        return pd.Series(sar, index=df.index)
    trend = 1  # 1 上涨, -1 下跌
    af = af_step
    ep = high[0]
    sar[0] = low[0]
    for i in range(1, n):
        sar[i] = sar[i - 1] + af * (ep - sar[i - 1])
        if trend == 1:
            if low[i] < sar[i]:
                trend = -1
                sar[i] = ep
                ep = low[i]
                af = af_step
            else:
                if high[i] > ep:
                    ep = high[i]
                    af = min(af + af_step, af_max)
                sar[i] = min(sar[i], low[i - 1], low[max(i - 2, 0)])
        else:
            if high[i] > sar[i]:
                trend = 1
                sar[i] = ep
                ep = high[i]
                af = af_step
            else:
                if low[i] < ep:
                    ep = low[i]
                    af = min(af + af_step, af_max)
                sar[i] = max(sar[i], high[i - 1], high[max(i - 2, 0)])
    return pd.Series(sar, index=df.index)


def VORTEX(df: pd.DataFrame, period: int = 14):
    """涡旋指标。返回 (vi_plus, vi_minus)。"""
    high, low, close = df["high"], df["low"], df["close"]
    tr = pd.concat([high - low, (high - close.shift()).abs(),
                    (low - close.shift()).abs()], axis=1).max(axis=1)
    vm_plus = (high - low.shift()).abs()
    vm_minus = (low - high.shift()).abs()
    tr_sum = tr.rolling(period).sum()
    vi_plus = vm_plus.rolling(period).sum() / tr_sum.replace(0, np.nan)
    vi_minus = vm_minus.rolling(period).sum() / tr_sum.replace(0, np.nan)
    return vi_plus, vi_minus


def TSI(series: pd.Series, long: int = 25, short: int = 13) -> pd.Series:
    """True Strength Index(真实强度指标)。"""
    diff = series.diff()
    abs_diff = diff.abs()
    ema1 = diff.ewm(span=long, adjust=False).mean().ewm(span=short, adjust=False).mean()
    ema2 = abs_diff.ewm(span=long, adjust=False).mean().ewm(span=short, adjust=False).mean()
    return 100 * ema1 / ema2.replace(0, np.nan)


def CHAIKIN_MONEY_FLOW(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """蔡金资金流 (CMF)。"""
    high, low, close, vol = df["high"], df["low"], df["close"], df["volume"]
    mfm = ((close - low) - (high - close)) / (high - low).replace(0, np.nan)
    mfv = mfm * vol
    return mfv.rolling(period).sum() / vol.rolling(period).sum().replace(0, np.nan)


def FORCE_INDEX(df: pd.DataFrame, period: int = 13) -> pd.Series:
    """强力指数 (Elder Force Index)。"""
    fi = df["close"].diff() * df["volume"]
    return fi.ewm(span=period, adjust=False).mean()


def EASE_OF_MOVEMENT(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """简易波动指标 (EOM)。"""
    high, low, vol = df["high"], df["low"], df["volume"]
    distance = ((high + low) / 2) - ((high.shift() + low.shift()) / 2)
    box_ratio = (vol / 1e8) / (high - low).replace(0, np.nan)
    emv = distance / box_ratio.replace(0, np.nan)
    return emv.rolling(period).mean()


def HURST_EXPONENT(series: pd.Series, max_lag: int = 20) -> float:
    """Hurst 指数(分形维度)。>0.5 趋势,<0.5 均值回归。"""
    s = series.dropna().values
    if len(s) < max_lag * 2:
        return float("nan")
    lags = range(2, max_lag)
    tau = [np.std(s[lag:] - s[:-lag]) for lag in lags]
    tau = [t if t > 0 else 1e-10 for t in tau]
    poly = np.polyfit(np.log(list(lags)), np.log(tau), 1)
    return float(poly[0])


def DI_PLUS_MINUS(df: pd.DataFrame, period: int = 14):
    """DMI 的 +DI / -DI(复用 ADX 内部计算)。"""
    adx, pdi, ndi = ADX(df, period)
    return pdi, ndi


def STOCH_RSI(series: pd.Series, period: int = 14, k_smooth: int = 3, d_smooth: int = 3):
    """随机 RSI。返回 (k, d)。"""
    rsi = RSI(series, period)
    rsi_min = rsi.rolling(period).min()
    rsi_max = rsi.rolling(period).max()
    stoch = (rsi - rsi_min) / (rsi_max - rsi_min).replace(0, np.nan) * 100
    k = stoch.rolling(k_smooth).mean()
    d = k.rolling(d_smooth).mean()
    return k, d


def TTM_SQUEEZE(df: pd.DataFrame, period: int = 20, bb_mult: float = 2.0, kc_mult: float = 1.5):
    """TTM 挤压:布林带在 Keltner 通道内 = 挤压(蓄势)。返回 (squeeze_on, momentum)。"""
    bb_up, bb_mid, bb_low = BB(df["close"], period, bb_mult)
    kc_up, kc_mid, kc_low = KELTNER(df, period, kc_mult)
    squeeze_on = (bb_up < kc_up) & (bb_low > kc_low)
    highest = df["high"].rolling(period).max()
    lowest = df["low"].rolling(period).min()
    mid = (highest + lowest) / 2
    momentum = df["close"] - (mid + bb_mid) / 2
    return squeeze_on, momentum
