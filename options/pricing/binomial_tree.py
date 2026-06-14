"""二叉树期权定价 — 支持欧式与美式。"""
from __future__ import annotations

import math

import numpy as np


def crr_price(S: float, K: float, T: float, r: float, sigma: float,
              n_steps: int = 200, q: float = 0.0,
              option_type: str = "C", american: bool = False) -> float:
    """Cox-Ross-Rubinstein 二叉树定价。

    american=True 时支持美式提前行权。
    """
    if T <= 0:
        if option_type.upper() == "C":
            return max(S - K, 0.0)
        return max(K - S, 0.0)

    dt = T / n_steps
    u = math.exp(sigma * math.sqrt(dt))
    d = 1.0 / u
    p = (math.exp((r - q) * dt) - d) / (u - d)
    disc = math.exp(-r * dt)

    # 终值
    j = np.arange(n_steps + 1)
    ST = S * (u ** (n_steps - j)) * (d ** j)
    if option_type.upper() == "C":
        V = np.maximum(ST - K, 0.0)
    else:
        V = np.maximum(K - ST, 0.0)

    # 反向递推
    for i in range(n_steps - 1, -1, -1):
        V = disc * (p * V[:-1] + (1 - p) * V[1:])
        if american:
            jj = np.arange(i + 1)
            St = S * (u ** (i - jj)) * (d ** jj)
            if option_type.upper() == "C":
                V = np.maximum(V, St - K)
            else:
                V = np.maximum(V, K - St)

    return float(V[0])
