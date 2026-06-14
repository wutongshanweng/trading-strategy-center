"""SABR 随机波动率模型 — Hagan (2002) 隐含波动率近似 + 校准。

dF = alpha * F^beta * dW1
d(alpha) = nu * alpha * dW2
corr(dW1, dW2) = rho

广泛用于利率/商品期权的波动率微笑建模。提供 Hagan 渐近隐含波动率公式
与基于市场报价的参数校准(固定 beta,拟合 alpha/rho/nu)。
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize


@dataclass
class SABRParams:
    alpha: float    # 初始波动率水平
    beta: float     # CEV 弹性 (0=正态, 1=对数正态)
    rho: float      # 相关系数
    nu: float       # vol of vol


def sabr_implied_vol(F: float, K: float, T: float, p: SABRParams) -> float:
    """Hagan 渐近公式计算 SABR 隐含波动率(Black 口径)。"""
    alpha, beta, rho, nu = p.alpha, p.beta, p.rho, p.nu
    if F <= 0 or K <= 0 or T <= 0 or alpha <= 0:
        return float("nan")

    if abs(F - K) < 1e-12:
        # ATM 极限
        fk_beta = F ** (1 - beta)
        term1 = alpha / fk_beta
        term2 = (((1 - beta) ** 2 / 24) * alpha ** 2 / fk_beta ** 2
                 + 0.25 * rho * beta * nu * alpha / fk_beta
                 + (2 - 3 * rho ** 2) / 24 * nu ** 2)
        return float(term1 * (1 + term2 * T))

    log_fk = math.log(F / K)
    fk_beta = (F * K) ** ((1 - beta) / 2)
    z = (nu / alpha) * fk_beta * log_fk
    x_z = math.log((math.sqrt(1 - 2 * rho * z + z ** 2) + z - rho) / (1 - rho))

    denom = fk_beta * (1
                       + (1 - beta) ** 2 / 24 * log_fk ** 2
                       + (1 - beta) ** 4 / 1920 * log_fk ** 4)
    factor = (((1 - beta) ** 2 / 24) * alpha ** 2 / fk_beta ** 2
              + 0.25 * rho * beta * nu * alpha / fk_beta
              + (2 - 3 * rho ** 2) / 24 * nu ** 2)
    vol = (alpha / denom) * (z / x_z) * (1 + factor * T)
    return float(vol)


def calibrate_sabr(F: float, strikes: np.ndarray, market_vols: np.ndarray,
                   T: float, beta: float = 0.5) -> SABRParams:
    """固定 beta,校准 (alpha, rho, nu) 拟合市场波动率微笑。"""
    strikes = np.asarray(strikes, dtype=float)
    market_vols = np.asarray(market_vols, dtype=float)

    def obj(x):
        alpha, rho, nu = x
        if alpha <= 0 or abs(rho) >= 1 or nu < 0:
            return 1e10
        p = SABRParams(alpha, beta, rho, nu)
        model = np.array([sabr_implied_vol(F, k, T, p) for k in strikes])
        if np.any(np.isnan(model)):
            return 1e10
        return float(np.sum((model - market_vols) ** 2))

    # 初值:ATM vol 作 alpha 起点
    atm_idx = int(np.argmin(np.abs(strikes - F)))
    x0 = [market_vols[atm_idx] * F ** (1 - beta), 0.0, 0.3]
    bounds = [(1e-4, 5.0), (-0.999, 0.999), (1e-4, 5.0)]
    res = minimize(obj, x0, bounds=bounds, method="L-BFGS-B")
    alpha, rho, nu = res.x
    return SABRParams(alpha, beta, rho, nu)
