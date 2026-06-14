"""BSM 解析希腊字母(也适用于 Black76:传 F 替代 S,设 q=r)。"""
from __future__ import annotations

import math
from dataclasses import dataclass

from scipy.stats import norm


@dataclass
class Greeks:
    """期权希腊字母。

    delta: 对标的价格 1.0 变化的敏感度
    gamma: delta 对标的价格的二阶敏感度
    vega:  对 1.0 (100%) vol 变化的敏感度,除以 100 得 1% vol 影响
    theta: 每年 theta,除以 365 得每日时间衰减
    rho:   对 1.0 (100%) 利率变化的敏感度
    """

    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float

    @property
    def vega_pct(self) -> float:
        """每 1% 波动率变化的影响。"""
        return self.vega / 100.0

    @property
    def theta_daily(self) -> float:
        """每日时间衰减(按 365 日)。"""
        return self.theta / 365.0


def bsm_greeks(S: float, K: float, T: float, r: float, sigma: float,
               q: float = 0.0, option_type: str = "C") -> Greeks:
    """BSM 解析希腊字母(股票/ETF 期权)。"""
    if T <= 0 or sigma <= 0:
        if option_type.upper() == "C":
            return Greeks(1.0 if S > K else 0.0, 0.0, 0.0, 0.0, 0.0)
        return Greeks(-1.0 if S < K else 0.0, 0.0, 0.0, 0.0, 0.0)

    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    pdf_d1 = norm.pdf(d1)
    e_qT = math.exp(-q * T)
    e_rT = math.exp(-r * T)

    gamma = e_qT * pdf_d1 / (S * sigma * sqrtT)
    vega = S * e_qT * pdf_d1 * sqrtT

    if option_type.upper() == "C":
        delta = e_qT * norm.cdf(d1)
        theta = (-S * e_qT * pdf_d1 * sigma / (2 * sqrtT)
                 + q * S * e_qT * norm.cdf(d1)
                 - r * K * e_rT * norm.cdf(d2))
        rho = K * T * e_rT * norm.cdf(d2)
    else:
        delta = -e_qT * norm.cdf(-d1)
        theta = (-S * e_qT * pdf_d1 * sigma / (2 * sqrtT)
                 - q * S * e_qT * norm.cdf(-d1)
                 + r * K * e_rT * norm.cdf(-d2))
        rho = -K * T * e_rT * norm.cdf(-d2)
    return Greeks(delta, gamma, vega, theta, rho)


def black76_greeks(F: float, K: float, T: float, r: float, sigma: float,
                   option_type: str = "C") -> Greeks:
    """Black76 期货期权希腊字母。"""
    if T <= 0 or sigma <= 0:
        if option_type.upper() == "C":
            return Greeks(math.exp(-r * T) if F > K else 0.0, 0.0, 0.0, 0.0, 0.0)
        return Greeks(-math.exp(-r * T) if F < K else 0.0, 0.0, 0.0, 0.0, 0.0)

    sqrtT = math.sqrt(T)
    d1 = (math.log(F / K) + 0.5 * sigma ** 2 * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    pdf_d1 = norm.pdf(d1)
    e_rT = math.exp(-r * T)

    gamma = e_rT * pdf_d1 / (F * sigma * sqrtT)
    vega = F * e_rT * pdf_d1 * sqrtT

    if option_type.upper() == "C":
        delta = e_rT * norm.cdf(d1)
        theta = (-F * e_rT * pdf_d1 * sigma / (2 * sqrtT)
                 - r * e_rT * (F * norm.cdf(d1) - K * norm.cdf(d2)))
        rho = K * T * e_rT * norm.cdf(d2)
    else:
        delta = -e_rT * norm.cdf(-d1)
        theta = (-F * e_rT * pdf_d1 * sigma / (2 * sqrtT)
                 + r * e_rT * (K * norm.cdf(-d2) - F * norm.cdf(-d1)))
        rho = -K * T * e_rT * norm.cdf(-d2)
    return Greeks(delta, gamma, vega, theta, rho)
