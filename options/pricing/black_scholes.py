"""Black-Scholes-Merton 解析定价。"""
from __future__ import annotations

import math

import numpy as np
from scipy.stats import norm


def bsm_price(S: float, K: float, T: float, r: float, sigma: float,
              q: float = 0.0, option_type: str = "C") -> float:
    """欧式期权 BSM 定价。

    S: 标的现价
    K: 行权价
    T: 到期时间(年)
    r: 无风险利率
    sigma: 波动率(年化)
    q: 连续股息率
    option_type: 'C' / 'P'
    """
    if T <= 0 or sigma <= 0:
        # 已到期或无波动 -> 内在价值
        if option_type.upper() == "C":
            return max(S - K, 0.0)
        return max(K - S, 0.0)

    d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    if option_type.upper() == "C":
        return S * math.exp(-q * T) * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    return K * math.exp(-r * T) * norm.cdf(-d2) - S * math.exp(-q * T) * norm.cdf(-d1)


def bsm_price_vec(S, K, T, r, sigma, q=0.0, option_type="C"):
    """向量化 BSM 定价(批量行权价/到期/波动率)。"""
    S, K, T, sigma = map(np.asarray, (S, K, T, sigma))
    with np.errstate(divide="ignore", invalid="ignore"):
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
    if option_type.upper() == "C":
        return S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)
