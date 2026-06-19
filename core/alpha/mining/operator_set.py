"""
基础算子集合 — 遗传因子挖掘的构建单元 (函数式入口)。

与 mining/__init__.py 的 OperatorLibrary (lambda 风格, GP 引擎内部用) 互补:
本模块提供**带参数的命名算子** + 统一注册表, 供表达式挖掘/外部调用。

算子分类:
  - ts_*  时间序列算子 (单条序列 -> 单条序列)
  - 双目  数学算子 (两条序列 -> 一条序列)

用法:
    from core.alpha.mining.operator_set import get_operators, apply_operator
    result = apply_operator("ts_rank", close, d=10)
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd


# ═══════════ 时间序列算子 ═══════════

def ts_rank(s: pd.Series, d: int = 5) -> pd.Series:
    """过去 d 天的排名百分位 (当前值在窗口内的分位)。"""
    return s.rolling(d, min_periods=max(1, d // 2)).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) > 0 else 0.5, raw=False)


def ts_sum(s: pd.Series, d: int = 5) -> pd.Series:
    return s.rolling(d, min_periods=1).sum()


def ts_mean(s: pd.Series, d: int = 5) -> pd.Series:
    return s.rolling(d, min_periods=1).mean()


def ts_std(s: pd.Series, d: int = 5) -> pd.Series:
    return s.rolling(d, min_periods=2).std()


def ts_min(s: pd.Series, d: int = 5) -> pd.Series:
    return s.rolling(d, min_periods=1).min()


def ts_max(s: pd.Series, d: int = 5) -> pd.Series:
    return s.rolling(d, min_periods=1).max()


def ts_argmax(s: pd.Series, d: int = 5) -> pd.Series:
    """过去 d 天中最大值出现在几天前 (0=今天)。"""
    return s.rolling(d, min_periods=1).apply(
        lambda x: (len(x) - 1 - int(np.argmax(x))) if len(x) > 0 else 0, raw=True)


def ts_argmin(s: pd.Series, d: int = 5) -> pd.Series:
    """过去 d 天中最小值出现在几天前 (0=今天)。"""
    return s.rolling(d, min_periods=1).apply(
        lambda x: (len(x) - 1 - int(np.argmin(x))) if len(x) > 0 else 0, raw=True)


def ts_corr(s1: pd.Series, s2: pd.Series, d: int = 5) -> pd.Series:
    """两条序列过去 d 天的滚动相关系数。"""
    return s1.rolling(d, min_periods=max(2, d // 2)).corr(s2)


def ts_cov(s1: pd.Series, s2: pd.Series, d: int = 5) -> pd.Series:
    """两条序列过去 d 天的滚动协方差。"""
    return s1.rolling(d, min_periods=max(2, d // 2)).cov(s2)


def delay(s: pd.Series, d: int = 1) -> pd.Series:
    """延迟 d 天。"""
    return s.shift(d)


def delta(s: pd.Series, d: int = 1) -> pd.Series:
    """当前值 - d 天前的值。"""
    return s - s.shift(d)


def ts_rank_decay(s: pd.Series, d: int = 5) -> pd.Series:
    """衰减加权移动平均 (近期权重更大, 线性衰减)。"""
    weights = np.arange(1, d + 1, dtype=float)
    weights /= weights.sum()
    return s.rolling(d, min_periods=1).apply(
        lambda x: float(np.dot(x, weights[-len(x):]) / weights[-len(x):].sum())
        if len(x) > 0 else np.nan, raw=True)


def scale(s: pd.Series, target: float = 1.0) -> pd.Series:
    """缩放到目标绝对值之和 (横截面归一化常用)。"""
    denom = s.abs().sum()
    return s / (denom + 1e-10) * target if denom else s * 0.0


def signed_power(s: pd.Series, exp: float = 2.0) -> pd.Series:
    """保号幂: sign(x) * |x|^exp。"""
    return np.sign(s) * (s.abs() ** exp)


# ═══════════ 数学算子 (双目) ═══════════

def op_add(s1: pd.Series, s2: pd.Series) -> pd.Series:
    return s1 + s2


def op_sub(s1: pd.Series, s2: pd.Series) -> pd.Series:
    return s1 - s2


def op_mul(s1: pd.Series, s2: pd.Series) -> pd.Series:
    return s1 * s2


def op_div(s1: pd.Series, s2: pd.Series) -> pd.Series:
    return s1 / (s2 + 1e-10)


def op_max(s1: pd.Series, s2: pd.Series) -> pd.Series:
    return pd.concat([s1, s2], axis=1).max(axis=1)


def op_min(s1: pd.Series, s2: pd.Series) -> pd.Series:
    return pd.concat([s1, s2], axis=1).min(axis=1)


# ═══════════ 注册表 ═══════════

TS_OPERATORS: Dict[str, Callable] = {
    "ts_rank": ts_rank, "ts_sum": ts_sum, "ts_mean": ts_mean, "ts_std": ts_std,
    "ts_min": ts_min, "ts_max": ts_max, "ts_argmax": ts_argmax, "ts_argmin": ts_argmin,
    "ts_corr": ts_corr, "ts_cov": ts_cov, "delay": delay, "delta": delta,
    "ts_rank_decay": ts_rank_decay, "scale": scale, "signed_power": signed_power,
}

MATH_OPERATORS: Dict[str, Callable] = {
    "op_add": op_add, "op_sub": op_sub, "op_mul": op_mul,
    "op_div": op_div, "op_max": op_max, "op_min": op_min,
}

# 需要两条序列输入的算子名 (挖掘时据此决定 arity)
BINARY_OPERATORS: List[str] = list(MATH_OPERATORS.keys()) + ["ts_corr", "ts_cov"]


def get_operator(name: str) -> Optional[Callable]:
    """按名称获取算子。"""
    return TS_OPERATORS.get(name) or MATH_OPERATORS.get(name)


def get_operators() -> Dict[str, Callable]:
    """获取所有算子 (ts + math)。"""
    return {**TS_OPERATORS, **MATH_OPERATORS}


def apply_operator(name: str, *args, **kwargs) -> pd.Series:
    """应用算子 (带参数)。未知算子抛 ValueError。"""
    op = get_operator(name)
    if op is None:
        raise ValueError(f"Unknown operator: {name}")
    return op(*args, **kwargs)
