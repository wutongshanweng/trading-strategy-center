"""短期利率模型 — Vasicek 与 CIR(国债期货、利率衍生品定价基础)。

Vasicek: dr = kappa*(theta - r)*dt + sigma*dW           (可为负)
CIR:     dr = kappa*(theta - r)*dt + sigma*sqrt(r)*dW    (恒非负)

提供:路径模拟、零息债券解析价格、基于历史利率序列的参数估计。
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass
class VasicekParams:
    kappa: float    # 均值回复速度
    theta: float    # 长期均值
    sigma: float    # 波动率
    r0: float       # 初始利率


def vasicek_simulate(p: VasicekParams, T: float, n_steps: int = 252,
                     n_paths: int = 1000, seed: int | None = None) -> np.ndarray:
    """Vasicek 利率路径模拟(精确离散化)。返回 (n_paths, n_steps+1)。"""
    rng = np.random.default_rng(seed)
    dt = T / n_steps
    r = np.zeros((n_paths, n_steps + 1))
    r[:, 0] = p.r0
    exp_kdt = math.exp(-p.kappa * dt)
    # 精确条件方差
    var = p.sigma ** 2 / (2 * p.kappa) * (1 - exp_kdt ** 2) if p.kappa > 0 else p.sigma ** 2 * dt
    std = math.sqrt(max(var, 0.0))
    for t in range(1, n_steps + 1):
        z = rng.standard_normal(n_paths)
        r[:, t] = p.theta + (r[:, t - 1] - p.theta) * exp_kdt + std * z
    return r


def vasicek_zcb_price(p: VasicekParams, T: float) -> float:
    """Vasicek 零息债券解析价格 P(0,T)(面值 1)。"""
    if p.kappa <= 0:
        return math.exp(-p.r0 * T)
    B = (1 - math.exp(-p.kappa * T)) / p.kappa
    A = math.exp((p.theta - p.sigma ** 2 / (2 * p.kappa ** 2)) * (B - T)
                 - p.sigma ** 2 / (4 * p.kappa) * B ** 2)
    return float(A * math.exp(-B * p.r0))


def estimate_vasicek(rates: np.ndarray, dt: float = 1 / 252) -> VasicekParams:
    """用 AR(1) 回归估计 Vasicek 参数(OLS)。

    r_{t+1} = a + b*r_t + e  =>  kappa = -ln(b)/dt, theta = a/(1-b)。
    """
    rates = np.asarray(rates, dtype=float)
    rates = rates[~np.isnan(rates)]
    if len(rates) < 3:
        raise ValueError("Need at least 3 rate observations")
    r_lag = rates[:-1]
    r_now = rates[1:]
    b, a = np.polyfit(r_lag, r_now, 1)
    b = min(max(b, 1e-6), 1 - 1e-6)
    kappa = -math.log(b) / dt
    theta = a / (1 - b)
    resid = r_now - (b * r_lag + a)
    sigma = float(np.std(resid) * math.sqrt(2 * kappa / (1 - b ** 2))) if kappa > 0 else float(np.std(resid))
    return VasicekParams(kappa=kappa, theta=theta, sigma=sigma, r0=float(rates[-1]))


@dataclass
class CIRParams:
    kappa: float
    theta: float
    sigma: float
    r0: float

    def feller_satisfied(self) -> bool:
        return 2 * self.kappa * self.theta > self.sigma ** 2


def cir_simulate(p: CIRParams, T: float, n_steps: int = 252,
                 n_paths: int = 1000, seed: int | None = None) -> np.ndarray:
    """CIR 利率路径模拟(全截断 Euler,保证非负)。"""
    rng = np.random.default_rng(seed)
    dt = T / n_steps
    r = np.zeros((n_paths, n_steps + 1))
    r[:, 0] = p.r0
    sqrt_dt = math.sqrt(dt)
    for t in range(1, n_steps + 1):
        r_prev = np.maximum(r[:, t - 1], 0.0)
        z = rng.standard_normal(n_paths)
        r[:, t] = (r_prev + p.kappa * (p.theta - r_prev) * dt
                   + p.sigma * np.sqrt(r_prev) * sqrt_dt * z)
        r[:, t] = np.maximum(r[:, t], 0.0)
    return r


def cir_zcb_price(p: CIRParams, T: float) -> float:
    """CIR 零息债券解析价格 P(0,T)(面值 1)。"""
    gamma = math.sqrt(p.kappa ** 2 + 2 * p.sigma ** 2)
    exp_gT = math.exp(gamma * T)
    denom = (gamma + p.kappa) * (exp_gT - 1) + 2 * gamma
    B = 2 * (exp_gT - 1) / denom
    A = ((2 * gamma * math.exp((p.kappa + gamma) * T / 2) / denom)
         ** (2 * p.kappa * p.theta / p.sigma ** 2))
    return float(A * math.exp(-B * p.r0))
