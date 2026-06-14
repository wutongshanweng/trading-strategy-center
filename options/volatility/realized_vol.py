"""已实现波动率 — 5 种主流估计量。"""
from __future__ import annotations

import numpy as np
import pandas as pd


def close_to_close(close: pd.Series, n: int = 20, annualize: int = 252) -> pd.Series:
    """收盘价对收盘价(最常用)。"""
    log_ret = np.log(close / close.shift(1))
    return log_ret.rolling(n).std(ddof=0) * np.sqrt(annualize)


def parkinson(high: pd.Series, low: pd.Series, n: int = 20, annualize: int = 252) -> pd.Series:
    """Parkinson 估计量(仅用高低点,效率高于 close-to-close)。"""
    factor = 1.0 / (4.0 * np.log(2.0))
    rs = factor * (np.log(high / low)) ** 2
    return np.sqrt(rs.rolling(n).mean() * annualize)


def garman_klass(open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series,
                 n: int = 20, annualize: int = 252) -> pd.Series:
    """Garman-Klass 估计量(用 OHLC)。"""
    log_hl = np.log(high / low)
    log_co = np.log(close / open_)
    rs = 0.5 * log_hl ** 2 - (2 * np.log(2) - 1) * log_co ** 2
    return np.sqrt(rs.rolling(n).mean() * annualize)


def rogers_satchell(open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series,
                    n: int = 20, annualize: int = 252) -> pd.Series:
    """Rogers-Satchell 估计量(允许漂移)。"""
    rs = (np.log(high / close) * np.log(high / open_) +
          np.log(low / close) * np.log(low / open_))
    return np.sqrt(rs.rolling(n).mean() * annualize)


def yang_zhang(open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series,
               n: int = 20, annualize: int = 252, k: float = 0.34) -> pd.Series:
    """Yang-Zhang 估计量(开盘跳空 + 隔夜 + 日内,最稳健)。"""
    log_oc_prev = np.log(open_ / close.shift(1))
    log_co = np.log(close / open_)
    rs_term = (np.log(high / close) * np.log(high / open_) +
               np.log(low / close) * np.log(low / open_))
    sigma_o = log_oc_prev.rolling(n).var(ddof=0)
    sigma_c = log_co.rolling(n).var(ddof=0)
    sigma_rs = rs_term.rolling(n).mean()
    sigma_yz = sigma_o + k * sigma_c + (1 - k) * sigma_rs
    return np.sqrt(sigma_yz * annualize)
