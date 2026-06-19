"""
因子衰减监控 — 自动检测因子何时失效 (三态健康评级)。

与已有 management/__init__.py 的 FactorMonitoring (基于版本自相关) 不同:
本模块基于 **IC 时间序列趋势 + 分层单调性** 做交易有效性评级, 面向因子下线决策。

检测维度:
  1. 当前 IC 绝对值 (低于阈值告警)
  2. IC 趋势斜率 (持续下降 = 衰减)
  3. 短/中/长期 IC 对比
  4. 分层单调性 (Q1->Q5 收益是否单调)

状态: HEALTHY (正常) / WARNING (需关注) / DECAYED (已失效, 建议下线)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats


class FactorHealth(Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    DECAYED = "DECAYED"


@dataclass
class FactorHealthReport:
    factor_name: str
    health: FactorHealth
    current_ic: float
    ic_trend: float                       # 正=改善, 负=衰减
    ic_mean_short: float                  # 短期 IC 均值
    ic_mean_long: float                   # 长期 IC 均值
    icir: float
    monotonicity: float                   # 分层单调性 -1~1 (|值|越大越单调)
    reasons: List[str] = field(default_factory=list)
    alert_level: str = "info"             # info / warning / critical


class FactorDecayDetector:
    """因子衰减检测器 — 基于 IC 序列与分层单调性的三态评级。"""

    def __init__(
        self,
        ic_threshold: float = 0.02,
        decay_slope_threshold: float = -0.0005,
        short_window: int = 60,
        long_window: int = 240,
        monotonicity_threshold: float = 0.5,
    ):
        self.ic_threshold = ic_threshold
        self.decay_slope_threshold = decay_slope_threshold
        self.short_window = short_window
        self.long_window = long_window
        self.monotonicity_threshold = monotonicity_threshold

    def check(
        self,
        factor_name: str,
        ic_series: pd.Series,
        factor_values: Optional[pd.Series] = None,
        forward_returns: Optional[pd.Series] = None,
        n_quantiles: int = 5,
    ) -> FactorHealthReport:
        """全面评估因子健康。

        Args:
            ic_series: 因子 IC 时间序列 (必需, 评级核心)。
            factor_values/forward_returns: 截面因子值与未来收益 (可选, 算单调性)。
        """
        ic_clean = ic_series.dropna()
        current_ic = float(ic_clean.iloc[-1]) if len(ic_clean) else 0.0
        trend = self._ic_trend(ic_clean)
        short = float(ic_clean.tail(self.short_window).mean()) if len(ic_clean) else 0.0
        long = float(ic_clean.tail(self.long_window).mean()) if len(ic_clean) else 0.0
        icir = self._icir(ic_clean)
        mono = (self._monotonicity(factor_values, forward_returns, n_quantiles)
                if factor_values is not None and forward_returns is not None else 0.0)

        reasons: List[str] = []
        # 用近期均值的绝对值衡量当前有效性 (比单点 IC 稳健)
        recent_abs = abs(short)
        if recent_abs < self.ic_threshold:
            reasons.append(f"近期|IC|={recent_abs:.4f} 低于阈值 {self.ic_threshold}")
        if trend < self.decay_slope_threshold:
            reasons.append(f"IC 趋势下行 (斜率={trend:.5f})")
        # 短期显著弱于长期 -> 衰减信号
        if abs(long) > 1e-6 and recent_abs < abs(long) * 0.5:
            reasons.append("近期 IC 不足长期一半, 明显衰减")
        if factor_values is not None and abs(mono) < self.monotonicity_threshold:
            reasons.append(f"分层单调性弱 ({mono:.2f})")

        # 评级
        decayed = (recent_abs < self.ic_threshold and trend < self.decay_slope_threshold) or \
                  (abs(long) > 1e-6 and recent_abs < abs(long) * 0.4)
        if decayed:
            health, alert = FactorHealth.DECAYED, "critical"
        elif reasons:
            health, alert = FactorHealth.WARNING, "warning"
        else:
            health, alert = FactorHealth.HEALTHY, "info"

        return FactorHealthReport(
            factor_name=factor_name, health=health, current_ic=round(current_ic, 4),
            ic_trend=round(trend, 6), ic_mean_short=round(short, 4),
            ic_mean_long=round(long, 4), icir=round(icir, 4),
            monotonicity=round(mono, 4), reasons=reasons, alert_level=alert,
        )

    @staticmethod
    def _ic_trend(ic: pd.Series) -> float:
        if len(ic) < 5:
            return 0.0
        x = np.arange(len(ic))
        slope = float(np.polyfit(x, ic.values, 1)[0])
        return slope

    @staticmethod
    def _icir(ic: pd.Series) -> float:
        if len(ic) < 2:
            return 0.0
        std = ic.std()
        return float(ic.mean() / std) if std else 0.0

    @staticmethod
    def _monotonicity(factor_values: pd.Series, forward_returns: pd.Series,
                      n_quantiles: int = 5) -> float:
        """分层单调性: 各分位组平均收益与分位序号的 Spearman 相关 (-1~1)。"""
        common = factor_values.index.intersection(forward_returns.index)
        fv = factor_values.loc[common].dropna()
        rv = forward_returns.loc[fv.index].dropna()
        fv = fv.loc[rv.index]
        if len(fv) < n_quantiles * 2:
            return 0.0
        try:
            q = pd.qcut(fv, n_quantiles, labels=False, duplicates="drop")
        except ValueError:
            return 0.0
        grp = rv.groupby(q).mean()
        if len(grp) < 3:
            return 0.0
        rho, _ = stats.spearmanr(grp.index, grp.values)
        return float(rho) if not np.isnan(rho) else 0.0

    def batch_check(
        self,
        ic_series_map: Dict[str, pd.Series],
    ) -> Dict[str, FactorHealthReport]:
        """批量检查多个因子的 IC 序列。"""
        return {name: self.check(name, ic) for name, ic in ic_series_map.items()}
