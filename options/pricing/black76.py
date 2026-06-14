"""Black-76 模型 — 期货期权定价(国内商品/股指期权主流)。"""
from __future__ import annotations

import math

from scipy.stats import norm


def black76_price(F: float, K: float, T: float, r: float, sigma: float,
                  option_type: str = "C") -> float:
    """期货期权 Black76 定价。

    F: 期货价格(标的)
    K: 行权价
    T: 到期时间(年)
    r: 无风险利率(用于贴现)
    sigma: 波动率(年化)
    option_type: 'C' / 'P'
    """
    if T <= 0 or sigma <= 0:
        if option_type.upper() == "C":
            return math.exp(-r * T) * max(F - K, 0.0)
        return math.exp(-r * T) * max(K - F, 0.0)

    d1 = (math.log(F / K) + 0.5 * sigma ** 2 * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    if option_type.upper() == "C":
        return math.exp(-r * T) * (F * norm.cdf(d1) - K * norm.cdf(d2))
    return math.exp(-r * T) * (K * norm.cdf(-d2) - F * norm.cdf(-d1))
