"""
因子分析器 - 用于因子研究的工具类
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from scipy import stats


class FactorAnalyzer:
    """因子分析工具"""

    def calculate_ic(
        self,
        factor_values: pd.Series,
        returns: pd.Series,
        method: str = 'pearson'
    ) -> float:
        """
        计算信息系数 (IC)

        Args:
            factor_values: 因子值
            returns: 未来收益率
            method: 'pearson' 或 'spearman'

        Returns:
            IC值
        """
        # 对齐索引
        common_idx = factor_values.index.intersection(returns.index)
        factor_aligned = factor_values.loc[common_idx]
        returns_aligned = returns.loc[common_idx]

        # 去除NaN
        valid_mask = ~(factor_aligned.isna() | returns_aligned.isna())
        factor_clean = factor_aligned[valid_mask]
        returns_clean = returns_aligned[valid_mask]

        if len(factor_clean) < 2:
            return np.nan

        if method == 'pearson':
            ic, _ = stats.pearsonr(factor_clean, returns_clean)
        elif method == 'spearman':
            ic, _ = stats.spearmanr(factor_clean, returns_clean)
        else:
            raise ValueError(f"Unknown method: {method}")

        return ic

    def calculate_ic_series(
        self,
        factor_df: pd.DataFrame,
        returns_df: pd.DataFrame,
        method: str = 'pearson'
    ) -> pd.Series:
        """
        计算时间序列IC

        Args:
            factor_df: 因子值 DataFrame [date x symbols]
            returns_df: 收益率 DataFrame [date x symbols]
            method: 相关系数方法

        Returns:
            每个时间点的IC值
        """
        ic_series = []
        dates = []

        for date in factor_df.index:
            if date not in returns_df.index:
                continue

            factor_cross = factor_df.loc[date]
            returns_cross = returns_df.loc[date]

            ic = self.calculate_ic(factor_cross, returns_cross, method)
            ic_series.append(ic)
            dates.append(date)

        return pd.Series(ic_series, index=dates, name='IC')

    def calculate_icir(self, ic_series: pd.Series) -> float:
        """
        计算信息比率 (ICIR = IC均值 / IC标准差)

        Args:
            ic_series: IC时间序列

        Returns:
            ICIR值
        """
        ic_mean = ic_series.mean()
        ic_std = ic_series.std()

        if ic_std == 0:
            return np.nan

        return ic_mean / ic_std

    def layered_backtest(
        self,
        factor_values: pd.Series,
        returns: pd.Series,
        n_quantiles: int = 5
    ) -> Dict:
        """
        分层回测

        将因子值分成N层，计算每层的平均收益

        Args:
            factor_values: 因子值
            returns: 收益率
            n_quantiles: 分层数量

        Returns:
            每层的统计信息
        """
        # 对齐数据
        common_idx = factor_values.index.intersection(returns.index)
        factor_aligned = factor_values.loc[common_idx]
        returns_aligned = returns.loc[common_idx]

        # 去除NaN
        valid_mask = ~(factor_aligned.isna() | returns_aligned.isna())
        factor_clean = factor_aligned[valid_mask]
        returns_clean = returns_aligned[valid_mask]

        # 分层
        quantiles = pd.qcut(factor_clean, q=n_quantiles, labels=False, duplicates='drop')

        # 计算每层统计
        results = {}
        for q in range(n_quantiles):
            mask = quantiles == q
            layer_returns = returns_clean[mask]

            results[f'Q{q+1}'] = {
                'mean_return': layer_returns.mean(),
                'std_return': layer_returns.std(),
                'sharpe': layer_returns.mean() / (layer_returns.std() + 1e-10) * np.sqrt(252),
                'count': len(layer_returns)
            }

        # 计算多空收益（最高层-最低层）
        if n_quantiles > 1:
            results['long_short'] = {
                'mean_return': results[f'Q{n_quantiles}']['mean_return'] - results['Q1']['mean_return'],
                'sharpe': (results[f'Q{n_quantiles}']['mean_return'] - results['Q1']['mean_return']) /
                         (np.sqrt(results[f'Q{n_quantiles}']['std_return']**2 + results['Q1']['std_return']**2) + 1e-10) * np.sqrt(252)
            }

        return results

    def ic_decay(
        self,
        factor_values: pd.Series,
        price_series: pd.Series,
        max_periods: int = 20
    ) -> pd.Series:
        """
        因子衰减分析

        计算因子对未来不同周期收益的预测能力

        Args:
            factor_values: 因子值
            price_series: 价格序列
            max_periods: 最大周期数

        Returns:
            不同周期的IC值
        """
        ic_values = []

        for period in range(1, max_periods + 1):
            # 计算period期后的收益
            returns = price_series.pct_change(period).shift(-period)

            # 计算IC
            ic = self.calculate_ic(factor_values, returns)
            ic_values.append(ic)

        return pd.Series(
            ic_values,
            index=range(1, max_periods + 1),
            name='IC_Decay'
        )

    def factor_turnover(
        self,
        factor_df: pd.DataFrame,
        n_quantiles: int = 5
    ) -> float:
        """
        计算因子换手率

        衡量因子稳定性

        Args:
            factor_df: 因子值时间序列 [date x symbols]
            n_quantiles: 分层数量

        Returns:
            平均换手率
        """
        turnovers = []

        for i in range(1, len(factor_df)):
            prev_date = factor_df.index[i-1]
            curr_date = factor_df.index[i]

            # 获取两期的因子值
            prev_factors = factor_df.loc[prev_date].dropna()
            curr_factors = factor_df.loc[curr_date].dropna()

            # 找到共同标的
            common_symbols = prev_factors.index.intersection(curr_factors.index)

            if len(common_symbols) < n_quantiles:
                continue

            # 分层
            prev_quantiles = pd.qcut(prev_factors[common_symbols], q=n_quantiles, labels=False, duplicates='drop')
            curr_quantiles = pd.qcut(curr_factors[common_symbols], q=n_quantiles, labels=False, duplicates='drop')

            # 计算变化比例
            changed = (prev_quantiles != curr_quantiles).sum()
            turnover = changed / len(common_symbols)
            turnovers.append(turnover)

        return np.mean(turnovers) if turnovers else np.nan

    def summary_statistics(
        self,
        factor_values: pd.Series,
        returns: pd.Series,
        n_quantiles: int = 5
    ) -> Dict:
        """
        生成因子分析摘要报告

        Args:
            factor_values: 因子值
            returns: 收益率
            n_quantiles: 分层数量

        Returns:
            完整的统计摘要
        """
        # IC分析
        ic = self.calculate_ic(factor_values, returns, method='pearson')
        rank_ic = self.calculate_ic(factor_values, returns, method='spearman')

        # 分层回测
        layered = self.layered_backtest(factor_values, returns, n_quantiles)

        # 汇总
        summary = {
            'IC': {
                'pearson_ic': ic,
                'spearman_ic': rank_ic,
            },
            'layered_backtest': layered,
            'factor_stats': {
                'mean': factor_values.mean(),
                'std': factor_values.std(),
                'skew': factor_values.skew(),
                'kurtosis': factor_values.kurtosis(),
            }
        }

        return summary
