"""数值差分希腊字母 — 高阶 Greeks(vanna/volga/charm/speed)。

适用于解析解不便推导的高阶敏感度,以及随机波动率/数值定价模型。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .analytical_greeks import Greeks, bsm_greeks, black76_greeks


@dataclass
class HighOrderGreeks:
    """高阶希腊字母。"""

    vanna: float   # dDelta/dVol = dVega/dSpot
    volga: float   # dVega/dVol (vomma)
    charm: float   # dDelta/dTime
    speed: float   # dGamma/dSpot
    color: float   # dGamma/dTime


def _price_fn(futures: bool) -> Callable:
    if futures:
        from options.pricing.black76 import black76_price
        return lambda S, K, T, r, sigma, q, ot: black76_price(S, K, T, r, sigma, ot)
    from options.pricing.black_scholes import bsm_price
    return lambda S, K, T, r, sigma, q, ot: bsm_price(S, K, T, r, sigma, q, ot)


def numerical_high_order_greeks(
    S: float, K: float, T: float, r: float, sigma: float,
    q: float = 0.0, option_type: str = "C", futures: bool = False,
    dS: float | None = None, dsigma: float = 1e-4, dT: float = 1e-5,
) -> HighOrderGreeks:
    """中心差分计算高阶希腊字母。"""
    price = _price_fn(futures)
    h = dS if dS is not None else S * 1e-4

    def greeks(s_, sig_):
        g = (black76_greeks(s_, K, T, r, sig_, option_type) if futures
             else bsm_greeks(s_, K, T, r, sig_, q, option_type))
        return g

    # vanna = dDelta/dVol
    delta_up = greeks(S, sigma + dsigma).delta
    delta_dn = greeks(S, sigma - dsigma).delta
    vanna = (delta_up - delta_dn) / (2 * dsigma)

    # volga = dVega/dVol
    vega_up = greeks(S, sigma + dsigma).vega
    vega_dn = greeks(S, sigma - dsigma).vega
    volga = (vega_up - vega_dn) / (2 * dsigma)

    # speed = dGamma/dSpot
    gamma_up = greeks(S + h, sigma).gamma
    gamma_dn = greeks(S - h, sigma).gamma
    speed = (gamma_up - gamma_dn) / (2 * h)

    # charm = dDelta/dTime (-d delta / dT, 用前向差分避免 T<=0)
    if T - dT > 0:
        delta_t_up = (black76_greeks(S, K, T + dT, r, sigma, option_type) if futures
                      else bsm_greeks(S, K, T + dT, r, sigma, q, option_type)).delta
        delta_t_dn = (black76_greeks(S, K, T - dT, r, sigma, option_type) if futures
                      else bsm_greeks(S, K, T - dT, r, sigma, q, option_type)).delta
        charm = -(delta_t_up - delta_t_dn) / (2 * dT)
        gamma_t_up = (black76_greeks(S, K, T + dT, r, sigma, option_type) if futures
                      else bsm_greeks(S, K, T + dT, r, sigma, q, option_type)).gamma
        gamma_t_dn = (black76_greeks(S, K, T - dT, r, sigma, option_type) if futures
                      else bsm_greeks(S, K, T - dT, r, sigma, q, option_type)).gamma
        color = -(gamma_t_up - gamma_t_dn) / (2 * dT)
    else:
        charm = 0.0
        color = 0.0

    return HighOrderGreeks(vanna, volga, charm, speed, color)


# ---------- 便捷单项数值 Greeks(中心差分) ----------

def _greeks_at(S, K, T, r, sigma, q, option_type, futures):
    return (black76_greeks(S, K, T, r, sigma, option_type) if futures
            else bsm_greeks(S, K, T, r, sigma, q, option_type))


def numerical_delta(S, K, T, r, sigma, q=0.0, option_type="C",
                    futures=False, dS=None):
    """中心差分 Delta = dPrice/dSpot。"""
    price = _price_fn(futures)
    h = dS if dS is not None else S * 1e-4
    up = price(S + h, K, T, r, sigma, q, option_type)
    dn = price(S - h, K, T, r, sigma, q, option_type)
    return (up - dn) / (2 * h)


def numerical_gamma(S, K, T, r, sigma, q=0.0, option_type="C",
                    futures=False, dS=None):
    """中心差分 Gamma = d2Price/dSpot2。"""
    price = _price_fn(futures)
    h = dS if dS is not None else S * 1e-4
    up = price(S + h, K, T, r, sigma, q, option_type)
    mid = price(S, K, T, r, sigma, q, option_type)
    dn = price(S - h, K, T, r, sigma, q, option_type)
    return (up - 2 * mid + dn) / (h * h)


def numerical_vega(S, K, T, r, sigma, q=0.0, option_type="C",
                   futures=False, dsigma=1e-4):
    """中心差分 Vega = dPrice/dVol(对 1.0 vol 变化)。"""
    price = _price_fn(futures)
    up = price(S, K, T, r, sigma + dsigma, q, option_type)
    dn = price(S, K, T, r, sigma - dsigma, q, option_type)
    return (up - dn) / (2 * dsigma)


def numerical_theta(S, K, T, r, sigma, q=0.0, option_type="C",
                    futures=False, dT=1e-4):
    """中心差分 Theta = -dPrice/dT(每年)。"""
    price = _price_fn(futures)
    if T - dT <= 0:
        return 0.0
    up = price(S, K, T + dT, r, sigma, q, option_type)
    dn = price(S, K, T - dT, r, sigma, q, option_type)
    return -(up - dn) / (2 * dT)


def numerical_greeks(S, K, T, r, sigma, q=0.0, option_type="C",
                     futures=False) -> Greeks:
    """用数值差分组装一套一阶 Greeks(便于与解析解交叉验证)。

    rho 用解析值(数值对 r 差分意义不大),其余为中心差分。
    """
    delta = numerical_delta(S, K, T, r, sigma, q, option_type, futures)
    gamma = numerical_gamma(S, K, T, r, sigma, q, option_type, futures)
    vega = numerical_vega(S, K, T, r, sigma, q, option_type, futures)
    theta = numerical_theta(S, K, T, r, sigma, q, option_type, futures)
    rho = _greeks_at(S, K, T, r, sigma, q, option_type, futures).rho
    return Greeks(delta, gamma, vega, theta, rho)


def vanna(S, K, T, r, sigma, q=0.0, option_type="C", futures=False):
    """Vanna = dDelta/dVol。"""
    return numerical_high_order_greeks(
        S, K, T, r, sigma, q, option_type, futures).vanna


def volga(S, K, T, r, sigma, q=0.0, option_type="C", futures=False):
    """Volga (Vomma) = dVega/dVol。"""
    return numerical_high_order_greeks(
        S, K, T, r, sigma, q, option_type, futures).volga


def charm(S, K, T, r, sigma, q=0.0, option_type="C", futures=False):
    """Charm = dDelta/dTime。"""
    return numerical_high_order_greeks(
        S, K, T, r, sigma, q, option_type, futures).charm
