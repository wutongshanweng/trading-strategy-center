"""
行业中性化 — 去除因子中的行业暴露偏差。

因子值可能受行业整体影响 (某行业普涨), 中性化后得到"行业内相对强弱"。

方法:
  1. neutralize_by_mean   — factor - 行业均值 (默认, 最快)
  2. neutralize_by_zscore — (factor - 行业均值) / 行业标准差 (考虑分散度)
  3. neutralize_by_regression — 对行业哑变量回归取残差 (最严谨)
  4. neutralize_market   — 去除大盘 Beta 暴露
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


class IndustryNeutralizer:
    """行业/市场中性化处理器 (横截面操作, index = 标的)。"""

    def neutralize_by_mean(
        self, factor_values: pd.Series, industry_labels: pd.Series,
    ) -> pd.Series:
        """行业均值中性化: factor - 行业均值。"""
        ind = industry_labels.reindex(factor_values.index)
        industry_mean = factor_values.groupby(ind).transform("mean")
        return factor_values - industry_mean

    def neutralize_by_zscore(
        self, factor_values: pd.Series, industry_labels: pd.Series,
    ) -> pd.Series:
        """行业 Z-score 中性化: (factor - 行业均值) / 行业标准差。"""
        ind = industry_labels.reindex(factor_values.index)
        industry_mean = factor_values.groupby(ind).transform("mean")
        industry_std = factor_values.groupby(ind).transform("std")
        return (factor_values - industry_mean) / (industry_std + 1e-10)

    def neutralize_by_regression(
        self, factor_values: pd.Series, industry_labels: pd.Series,
    ) -> pd.Series:
        """行业回归中性化: 对行业哑变量做 OLS 取残差 (numpy 实现, 不引依赖)。"""
        valid = factor_values.dropna()
        ind = industry_labels.reindex(valid.index).fillna("__NA__")
        dummies = pd.get_dummies(ind).values.astype(float)
        # 加截距列
        X = np.column_stack([np.ones(len(valid)), dummies])
        y = valid.values.astype(float)
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        resid = y - X @ beta
        out = pd.Series(np.nan, index=factor_values.index, name=factor_values.name)
        out.loc[valid.index] = resid
        return out

    def neutralize_market(
        self, factor_values: pd.Series, market_factor: pd.Series,
    ) -> pd.Series:
        """市场中性化: 对市场因子回归取残差, 去除大盘暴露。"""
        common = factor_values.index.intersection(market_factor.index)
        f = factor_values.loc[common].dropna()
        m = market_factor.loc[f.index].dropna()
        f = f.loc[m.index]
        if len(f) < 3:
            return factor_values
        X = np.column_stack([np.ones(len(f)), m.values.astype(float)])
        beta, *_ = np.linalg.lstsq(X, f.values.astype(float), rcond=None)
        resid = f.values - X @ beta
        out = pd.Series(np.nan, index=factor_values.index, name=factor_values.name)
        out.loc[f.index] = resid
        return out

    @staticmethod
    def max_industry_exposure(
        factor_values: pd.Series, industry_labels: pd.Series,
    ) -> float:
        """最大行业暴露 = 各行业因子均值绝对值的最大者 (中性化效果度量)。"""
        ind = industry_labels.reindex(factor_values.index)
        means = factor_values.groupby(ind).mean().abs()
        return float(means.max()) if len(means) else 0.0
