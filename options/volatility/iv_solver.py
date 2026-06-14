"""隐含波动率反求 — Newton-Raphson + Brent fallback。"""
from __future__ import annotations

import math
from typing import Callable

from scipy.optimize import brentq
from scipy.stats import norm

from options.pricing.black_scholes import bsm_price
from options.pricing.black76 import black76_price


def implied_vol_brent(target_price: float, S: float, K: float, T: float, r: float,
                      q: float = 0.0, option_type: str = "C",
                      futures: bool = False, lo: float = 1e-4, hi: float = 5.0) -> float:
    """用 Brent 求解 IV,稳定但慢。

    futures=True 时使用 Black76(S 当作期货价 F)。
    无解时返回 nan。
    """
    if target_price <= 0 or T <= 0:
        return float("nan")

    if futures:
        pricer: Callable[[float], float] = lambda sigma: black76_price(S, K, T, r, sigma, option_type) - target_price
    else:
        pricer = lambda sigma: bsm_price(S, K, T, r, sigma, q, option_type) - target_price

    try:
        return brentq(pricer, lo, hi, xtol=1e-6)
    except ValueError:
        return float("nan")


def implied_vol_newton(target_price: float, S: float, K: float, T: float, r: float,
                       q: float = 0.0, option_type: str = "C",
                       futures: bool = False, init_sigma: float = 0.3,
                       max_iter: int = 50, tol: float = 1e-6) -> float:
    """Newton-Raphson 求 IV;失败回退 Brent。"""
    if target_price <= 0 or T <= 0:
        return float("nan")

    sigma = init_sigma
    for _ in range(max_iter):
        if futures:
            price = black76_price(S, K, T, r, sigma, option_type)
            d1 = (math.log(S / K) + 0.5 * sigma ** 2 * T) / (sigma * math.sqrt(T))
            vega = S * math.exp(-r * T) * norm.pdf(d1) * math.sqrt(T)
        else:
            price = bsm_price(S, K, T, r, sigma, q, option_type)
            d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
            vega = S * math.exp(-q * T) * norm.pdf(d1) * math.sqrt(T)

        diff = price - target_price
        if abs(diff) < tol:
            return sigma
        if vega < 1e-10:
            break
        sigma -= diff / vega
        if sigma <= 0 or sigma > 5:
            break

    return implied_vol_brent(target_price, S, K, T, r, q, option_type, futures)
