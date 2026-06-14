"""组合优化模型 — 风险平价 / HRP / 最小方差 / 最大分散化 / 逆波动率。

输入为资产收益率 DataFrame(列=资产,行=时间),输出为权重向量(和为 1)。
不依赖 cvxpy,均用 numpy/scipy 闭式或数值优化实现。
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage
from scipy.optimize import minimize
from scipy.spatial.distance import squareform


def _cov(returns: pd.DataFrame) -> np.ndarray:
    return returns.cov().values


def inverse_vol_weights(returns: pd.DataFrame) -> pd.Series:
    """逆波动率加权:权重 ∝ 1/sigma_i。"""
    vol = returns.std(ddof=0)
    inv = 1.0 / vol.replace(0, np.nan)
    w = inv / inv.sum()
    return w.fillna(0.0)


def min_variance_weights(returns: pd.DataFrame,
                         long_only: bool = True) -> pd.Series:
    """最小方差组合:min w'Σw s.t. sum(w)=1。"""
    cov = _cov(returns)
    n = cov.shape[0]
    if long_only:
        def obj(w):
            return w @ cov @ w
        cons = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
        bounds = [(0.0, 1.0)] * n
        res = minimize(obj, np.repeat(1 / n, n), method="SLSQP",
                       bounds=bounds, constraints=cons)
        w = res.x
    else:
        inv = np.linalg.pinv(cov)
        ones = np.ones(n)
        w = inv @ ones / (ones @ inv @ ones)
    return pd.Series(w, index=returns.columns)


def max_diversification_weights(returns: pd.DataFrame) -> pd.Series:
    """最大分散化:最大化 (w·sigma) / sqrt(w'Σw)。"""
    cov = _cov(returns)
    vol = returns.std(ddof=0).values
    n = len(vol)

    def neg_div_ratio(w):
        port_vol = math.sqrt(w @ cov @ w)
        weighted_vol = w @ vol
        return -weighted_vol / max(port_vol, 1e-12)

    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    bounds = [(0.0, 1.0)] * n
    res = minimize(neg_div_ratio, np.repeat(1 / n, n), method="SLSQP",
                   bounds=bounds, constraints=cons)
    return pd.Series(res.x, index=returns.columns)


def risk_parity_weights(returns: pd.DataFrame,
                        max_iter: int = 1000, tol: float = 1e-8) -> pd.Series:
    """风险平价:每个资产对组合风险的边际贡献相等。

    用循环坐标下降(Spinu 2013 风格)求解,稳定且无需外部凸优化库。
    """
    cov = _cov(returns)
    n = cov.shape[0]
    w = np.repeat(1 / n, n)
    target = 1.0 / n

    for _ in range(max_iter):
        w_prev = w.copy()
        port_var = w @ cov @ w
        mrc = cov @ w                      # 边际风险贡献
        rc = w * mrc / max(port_var, 1e-18)  # 风险贡献占比
        # 朝目标风险贡献调整
        w = w * (target / np.maximum(rc, 1e-18)) ** 0.5
        w = np.maximum(w, 0.0)
        w = w / w.sum()
        if np.max(np.abs(w - w_prev)) < tol:
            break
    return pd.Series(w, index=returns.columns)


def _get_quasi_diag(link: np.ndarray) -> list:
    """HRP:从层次聚类树恢复准对角排序。"""
    link = link.astype(int)
    sort_ix = pd.Series([link[-1, 0], link[-1, 1]])
    num_items = link[-1, 3]
    while sort_ix.max() >= num_items:
        sort_ix.index = range(0, sort_ix.shape[0] * 2, 2)
        df0 = sort_ix[sort_ix >= num_items]
        i = df0.index
        j = df0.values - num_items
        sort_ix[i] = link[j, 0]
        df1 = pd.Series(link[j, 1], index=i + 1)
        sort_ix = pd.concat([sort_ix, df1]).sort_index()
        sort_ix.index = range(sort_ix.shape[0])
    return sort_ix.tolist()


def _get_cluster_var(cov: np.ndarray, items: list) -> float:
    sub = cov[np.ix_(items, items)]
    ivp = 1.0 / np.diag(sub)
    ivp /= ivp.sum()
    return float(ivp @ sub @ ivp)


def _recursive_bisection(cov: np.ndarray, sort_ix: list) -> np.ndarray:
    w = np.ones(len(sort_ix))
    clusters = [sort_ix]
    while clusters:
        new_clusters = []
        for cl in clusters:
            if len(cl) <= 1:
                continue
            half = len(cl) // 2
            left, right = cl[:half], cl[half:]
            var_left = _get_cluster_var(cov, left)
            var_right = _get_cluster_var(cov, right)
            alpha = 1 - var_left / (var_left + var_right)
            for i in left:
                w[sort_ix.index(i)] *= alpha
            for i in right:
                w[sort_ix.index(i)] *= (1 - alpha)
            new_clusters += [left, right]
        clusters = new_clusters
    return w


def hrp_weights(returns: pd.DataFrame) -> pd.Series:
    """层次风险平价 (López de Prado 2016)。

    1) 相关->距离 2) 层次聚类 3) 准对角化 4) 递归二分配权。
    对协方差估计误差的鲁棒性优于 Markowitz。
    """
    corr = returns.corr().values
    cov = _cov(returns)
    n = corr.shape[0]
    if n == 1:
        return pd.Series([1.0], index=returns.columns)
    dist = np.sqrt(np.clip((1 - corr) / 2, 0, 1))
    np.fill_diagonal(dist, 0.0)
    condensed = squareform(dist, checks=False)
    link = linkage(condensed, method="single")
    sort_ix = _get_quasi_diag(link)
    w = _recursive_bisection(cov, sort_ix)
    return pd.Series(w, index=returns.columns)


def risk_contributions(weights: pd.Series, returns: pd.DataFrame) -> pd.Series:
    """计算各资产对组合方差的风险贡献占比(用于校验风险平价)。"""
    cov = _cov(returns)
    w = weights.values
    port_var = w @ cov @ w
    rc = w * (cov @ w) / max(port_var, 1e-18)
    return pd.Series(rc, index=returns.columns)
