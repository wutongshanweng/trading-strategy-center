"""Heston 随机波动率模型 — 半解析期权定价 + 蒙特卡洛路径模拟。

dS = mu*S*dt + sqrt(v)*S*dW1
dv = kappa*(theta - v)*dt + xi*sqrt(v)*dW2
corr(dW1, dW2) = rho

定价用 Heston (1993) 特征函数 + 数值积分(Gauss-Legendre)。
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass
class HestonParams:
    kappa: float    # 均值回复速度
    theta: float    # 长期方差
    xi: float       # 波动率的波动率 (vol of vol)
    rho: float      # 价格与波动率相关系数
    v0: float       # 初始方差

    def feller_satisfied(self) -> bool:
        """Feller 条件:2*kappa*theta > xi^2 时方差过程恒正。"""
        return 2 * self.kappa * self.theta > self.xi ** 2


def _heston_char_func(phi: complex, S: float, K: float, T: float, r: float,
                      p: HestonParams) -> complex:
    """Heston 特征函数(little Heston trap 形式,数值更稳定)。"""
    x = math.log(S)
    a = p.kappa * p.theta
    b = p.kappa
    rho, sigma, v0 = p.rho, p.xi, p.v0

    d = np.sqrt((rho * sigma * 1j * phi - b) ** 2 + sigma ** 2 * (1j * phi + phi ** 2))
    g = (b - rho * sigma * 1j * phi - d) / (b - rho * sigma * 1j * phi + d)

    exp_dt = np.exp(-d * T)
    C = (r * 1j * phi * T
         + a / sigma ** 2 * ((b - rho * sigma * 1j * phi - d) * T
                             - 2 * np.log((1 - g * exp_dt) / (1 - g))))
    D = ((b - rho * sigma * 1j * phi - d) / sigma ** 2
         * ((1 - exp_dt) / (1 - g * exp_dt)))
    return np.exp(C + D * v0 + 1j * phi * x)


def heston_price(S: float, K: float, T: float, r: float, p: HestonParams,
                 option_type: str = "C", n_points: int = 128,
                 u_max: float = 100.0) -> float:
    """Heston 欧式期权半解析定价(特征函数 + Gauss-Legendre 积分)。"""
    if T <= 0:
        if option_type.upper() == "C":
            return max(S - K, 0.0)
        return max(K - S, 0.0)

    nodes, weights = np.polynomial.legendre.leggauss(n_points)
    # 映射 [-1,1] -> (0, u_max]
    u = 0.5 * u_max * (nodes + 1)
    w = 0.5 * u_max * weights

    def integrand(j: int) -> float:
        total = 0.0
        for ui, wi in zip(u, w):
            if j == 1:
                num = np.exp(-1j * ui * math.log(K)) * _heston_char_func(ui - 1j, S, K, T, r, p)
                denom = 1j * ui * _heston_char_func(-1j, S, K, T, r, p)
            else:
                num = np.exp(-1j * ui * math.log(K)) * _heston_char_func(ui, S, K, T, r, p)
                denom = 1j * ui
            total += wi * np.real(num / denom)
        return total

    P1 = 0.5 + integrand(1) / math.pi
    P2 = 0.5 + integrand(2) / math.pi

    call = S * P1 - K * math.exp(-r * T) * P2
    if option_type.upper() == "C":
        return float(max(call, 0.0))
    # put-call parity
    put = call - S + K * math.exp(-r * T)
    return float(max(put, 0.0))


def heston_simulate(S0: float, T: float, r: float, p: HestonParams,
                    n_steps: int = 252, n_paths: int = 10000,
                    seed: int | None = None) -> Tuple[np.ndarray, np.ndarray]:
    """Heston 路径模拟(全截断 Euler 格式,保证方差非负)。

    返回 (价格路径, 方差路径),形状均为 (n_paths, n_steps+1)。
    """
    rng = np.random.default_rng(seed)
    dt = T / n_steps
    S = np.zeros((n_paths, n_steps + 1))
    v = np.zeros((n_paths, n_steps + 1))
    S[:, 0] = S0
    v[:, 0] = p.v0

    sqrt_dt = math.sqrt(dt)
    for t in range(1, n_steps + 1):
        z1 = rng.standard_normal(n_paths)
        z2 = p.rho * z1 + math.sqrt(1 - p.rho ** 2) * rng.standard_normal(n_paths)
        v_prev = v[:, t - 1]
        v_pos = np.maximum(v_prev, 0.0)
        v[:, t] = (v_prev + p.kappa * (p.theta - v_pos) * dt
                   + p.xi * np.sqrt(v_pos) * sqrt_dt * z2)
        v[:, t] = np.maximum(v[:, t], 0.0)
        S[:, t] = S[:, t - 1] * np.exp((r - 0.5 * v_pos) * dt
                                       + np.sqrt(v_pos) * sqrt_dt * z1)
    return S, v


def heston_mc_price(S0: float, K: float, T: float, r: float, p: HestonParams,
                    option_type: str = "C", n_steps: int = 100,
                    n_paths: int = 20000, seed: int | None = None) -> float:
    """蒙特卡洛交叉验证 Heston 定价。"""
    S, _ = heston_simulate(S0, T, r, p, n_steps, n_paths, seed)
    ST = S[:, -1]
    if option_type.upper() == "C":
        payoff = np.maximum(ST - K, 0.0)
    else:
        payoff = np.maximum(K - ST, 0.0)
    return float(math.exp(-r * T) * payoff.mean())
