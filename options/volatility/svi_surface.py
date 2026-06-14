"""SVI (Stochastic Volatility Inspired) 隐含波动率曲面。"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize


def svi_total_variance(k: np.ndarray, a: float, b: float, rho: float,
                       m: float, sigma: float) -> np.ndarray:
    """Gatheral raw SVI 参数化。

    w(k) = a + b * (rho*(k-m) + sqrt((k-m)^2 + sigma^2))
    k: log-moneyness = log(K/F)
    返回 total variance w = T * iv^2
    """
    return a + b * (rho * (k - m) + np.sqrt((k - m) ** 2 + sigma ** 2))


def fit_svi_slice(k: np.ndarray, w_market: np.ndarray, weights: np.ndarray | None = None):
    """单个到期日切片的 SVI 拟合。

    k: log-moneyness 数组
    w_market: 市场 total variance (T * iv^2)
    返回 [a, b, rho, m, sigma]
    """
    k = np.asarray(k, dtype=float)
    w_market = np.asarray(w_market, dtype=float)
    if weights is None:
        weights = np.ones_like(w_market)

    def obj(params):
        a, b, rho, m, sig = params
        if b < 0 or sig <= 0 or abs(rho) >= 1:
            return 1e10
        w_model = svi_total_variance(k, a, b, rho, m, sig)
        return float(np.sum(weights * (w_model - w_market) ** 2))

    x0 = [max(w_market.mean(), 1e-3), 0.1, 0.0, 0.0, 0.1]
    bounds = [(-1, 5), (0, 5), (-0.999, 0.999), (-2, 2), (1e-3, 5)]
    res = minimize(obj, x0, bounds=bounds, method="L-BFGS-B")
    return res.x


def svi_iv(k: np.ndarray, T: float, params) -> np.ndarray:
    """从 SVI 参数推 IV(K, T)。"""
    w = svi_total_variance(np.asarray(k, dtype=float), *params)
    return np.sqrt(np.maximum(w / T, 1e-9))
