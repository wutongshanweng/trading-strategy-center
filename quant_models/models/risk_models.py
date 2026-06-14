"""风险度量模型 — VaR / CVaR / EVT / 最大回撤 / 相关性破裂。

对齐《架构升级建议》risk_models/ 目录:
  - 历史 / 参数 / 蒙特卡洛 VaR
  - CVaR (Expected Shortfall)
  - 极值理论 (EVT, POT + GPD)
  - 最大回撤与回撤持续期
  - 相关性破裂检测

所有函数接受收益率序列(pd.Series / np.ndarray),返回标量或字典。
约定:损失为正口径的 VaR 返回正数(表示"在 alpha 置信下的潜在损失幅度")。
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def _to_returns(returns) -> np.ndarray:
    arr = np.asarray(returns, dtype=float)
    return arr[~np.isnan(arr)]


def historical_var(returns, alpha: float = 0.95) -> float:
    """历史模拟法 VaR。返回正数(损失幅度)。

    alpha=0.95 表示 95% 置信度下的单期最大损失。
    """
    r = _to_returns(returns)
    if r.size == 0:
        return float("nan")
    q = np.quantile(r, 1 - alpha)
    return float(-q)


def parametric_var(returns, alpha: float = 0.95) -> float:
    """参数法(正态假设)VaR。"""
    r = _to_returns(returns)
    if r.size < 2:
        return float("nan")
    mu, sigma = r.mean(), r.std(ddof=1)
    z = stats.norm.ppf(1 - alpha)
    return float(-(mu + sigma * z))


def monte_carlo_var(returns, alpha: float = 0.95,
                    n_sims: int = 100_000, seed: int | None = 42) -> float:
    """蒙特卡洛 VaR(从拟合正态分布抽样)。"""
    r = _to_returns(returns)
    if r.size < 2:
        return float("nan")
    rng = np.random.default_rng(seed)
    mu, sigma = r.mean(), r.std(ddof=1)
    sims = rng.normal(mu, sigma, n_sims)
    return float(-np.quantile(sims, 1 - alpha))


def cvar(returns, alpha: float = 0.95) -> float:
    """条件 VaR / Expected Shortfall:超过 VaR 的尾部平均损失。"""
    r = _to_returns(returns)
    if r.size == 0:
        return float("nan")
    var_threshold = np.quantile(r, 1 - alpha)
    tail = r[r <= var_threshold]
    if tail.size == 0:
        return float(-var_threshold)
    return float(-tail.mean())


# 描述性别名(与历史模拟 VaR 命名对齐)
historical_cvar = cvar
expected_shortfall = cvar


def evt_var_cvar(returns, alpha: float = 0.99,
                 threshold_pct: float = 0.90) -> dict:
    """极值理论 (POT + 广义帕累托分布) 估计极端 VaR/CVaR。

    threshold_pct: 用收益率分布该分位作为超阈值门限 u。
    返回 {var, cvar, xi(形状), beta(尺度), u(阈值), n_exceed}。
    """
    r = _to_returns(returns)
    losses = -r  # 转成损失口径
    if losses.size < 30:
        return {"var": float("nan"), "cvar": float("nan"),
                "xi": float("nan"), "beta": float("nan"),
                "u": float("nan"), "n_exceed": 0}

    u = np.quantile(losses, threshold_pct)
    exceed = losses[losses > u] - u
    n = losses.size
    nu = exceed.size
    if nu < 5:
        return {"var": float("nan"), "cvar": float("nan"),
                "xi": float("nan"), "beta": float("nan"),
                "u": float(u), "n_exceed": int(nu)}

    # 拟合 GPD
    xi, _, beta = stats.genpareto.fit(exceed, floc=0)

    # POT 公式
    p = 1 - alpha
    var = u + (beta / xi) * (((n / nu) * p) ** (-xi) - 1) if abs(xi) > 1e-8 \
        else u + beta * np.log((n / nu) / (n * p))
    if xi < 1:
        cvar_val = (var + beta - xi * u) / (1 - xi)
    else:
        cvar_val = float("inf")
    return {"var": float(var), "cvar": float(cvar_val),
            "xi": float(xi), "beta": float(beta),
            "u": float(u), "n_exceed": int(nu)}


def max_drawdown(equity_or_returns, is_returns: bool = True) -> dict:
    """最大回撤及其持续期。

    is_returns=True 时输入为收益率序列(内部累乘成净值);
    否则视为净值/权益曲线。
    返回 {max_drawdown(负数), peak_idx, trough_idx, duration}。
    """
    x = np.asarray(equity_or_returns, dtype=float)
    x = x[~np.isnan(x)]
    if x.size == 0:
        return {"max_drawdown": float("nan"), "peak_idx": -1,
                "trough_idx": -1, "duration": 0}
    equity = np.cumprod(1 + x) if is_returns else x
    running_max = np.maximum.accumulate(equity)
    drawdown = equity / running_max - 1
    trough = int(np.argmin(drawdown))
    peak = int(np.argmax(equity[:trough + 1])) if trough > 0 else 0
    return {"max_drawdown": float(drawdown.min()),
            "peak_idx": peak, "trough_idx": trough,
            "duration": int(trough - peak)}


def correlation_breakdown(returns_df: pd.DataFrame, window: int = 60,
                          stress_quantile: float = 0.05) -> dict:
    """相关性破裂检测:对比正常期 vs 压力期(尾部)的平均相关性。

    压力期定义为组合等权收益落在最差 stress_quantile 分位的样本。
    返回 {normal_corr, stress_corr, breakdown(stress-normal)}。
    """
    df = returns_df.dropna()
    if df.shape[0] < window or df.shape[1] < 2:
        return {"normal_corr": float("nan"), "stress_corr": float("nan"),
                "breakdown": float("nan")}
    port = df.mean(axis=1)
    cutoff = port.quantile(stress_quantile)
    stress_mask = port <= cutoff

    def avg_offdiag(corr: pd.DataFrame) -> float:
        m = corr.values
        iu = np.triu_indices_from(m, k=1)
        return float(np.nanmean(m[iu]))

    normal_corr = avg_offdiag(df[~stress_mask].corr())
    stress_corr = avg_offdiag(df[stress_mask].corr())
    return {"normal_corr": normal_corr, "stress_corr": stress_corr,
            "breakdown": stress_corr - normal_corr}
