"""
多数据源交叉验证系统。

核心功能:
1. 跨数据源一致性校验 (AKShare vs TDX vs YFinance)
2. 数据质量评分 (0-100)
3. 异常值检测 (价格突变/成交量异常/缺口)
4. 缺失值报告
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..core.base_fetcher import KlineData, KlineInterval
from ..core.data_source import DataSourceManager

logger = logging.getLogger(__name__)


@dataclass
class QualityReport:
    """数据质量报告"""
    symbol: str
    source: str
    score: float                  # 0-100
    total_bars: int
    missing_bars: int
    anomaly_count: int
    gap_count: int
    max_gap_days: int
    price_anomaly_count: int
    volume_anomaly_count: int
    details: List[str] = field(default_factory=list)
    checked_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CrossValidationResult:
    """交叉验证结果"""
    symbol: str
    interval: str
    sources_available: List[str]
    correlation: float            # 数据源间相关系数
    price_deviation_pct: float    # 最大价格偏差
    volume_deviation_pct: float   # 最大成交量偏差
    is_consistent: bool
    details: List[str] = field(default_factory=list)


class DataVerifier:
    """
    数据校验器 — 多数据源交叉验证 + 质量评分。
    """

    def __init__(self, source_mgr: DataSourceManager):
        self._source_mgr = source_mgr

    def check_quality(self, data: KlineData) -> QualityReport:
        """检查单个数据源的数据质量"""
        n = len(data.close)
        if n == 0:
            return QualityReport(
                symbol=data.symbol, source=data.source,
                score=0, total_bars=0, missing_bars=0,
                anomaly_count=0, gap_count=0, max_gap_days=0,
                price_anomaly_count=0, volume_anomaly_count=0,
                details=["No data"],
            )

        details = []
        missing = 0
        gaps = 0
        max_gap = 0
        price_anomalies = 0
        volume_anomalies = 0

        # 1. 检查缺失值
        for arr_name in ["open", "high", "low", "close", "volume"]:
            arr = getattr(data, arr_name, [])
            missing += sum(1 for v in arr if v is None or (isinstance(v, float) and np.isnan(v)))

        if missing > 0:
            details.append(f"缺失值: {missing}")

        # 2. 检查时间序列缺口
        if len(data.timestamps) > 1:
            for i in range(1, len(data.timestamps)):
                if isinstance(data.timestamps[i], datetime) and isinstance(data.timestamps[i-1], datetime):
                    gap = (data.timestamps[i] - data.timestamps[i-1]).days
                    max_gap = max(max_gap, gap)
                    if gap > 5:  # 交易日间隔不超过5天
                        gaps += 1

        if gaps > 0:
            details.append(f"时间缺口: {gaps}次 (最大{max_gap}天)")

        # 3. 检查价格异常 (单日涨跌幅 > 10%)
        if n > 1:
            closes = np.array(data.close, dtype=float)
            returns = np.abs(np.diff(closes) / (closes[:-1] + 1e-10))
            price_anomalies = int(np.sum(returns > 0.10))
            if price_anomalies > 0:
                details.append(f"价格异常(>10%): {price_anomalies}次")

        # 4. 检查成交量异常
        if n > 1:
            volumes = np.array(data.volume, dtype=float)
            vol_mean = np.mean(volumes[volumes > 0]) if np.any(volumes > 0) else 0
            if vol_mean > 0:
                vol_ratio = volumes / (vol_mean + 1e-10)
                volume_anomalies = int(np.sum(vol_ratio > 5))
                if volume_anomalies > 0:
                    details.append(f"成交量异常(>5倍均值): {volume_anomalies}次")

        # 5. 计算综合评分
        score = 100.0
        score -= missing * 0.5
        score -= gaps * 2.0
        score -= price_anomalies * 5.0
        score -= volume_anomalies * 2.0
        score = max(0, min(100, score))

        return QualityReport(
            symbol=data.symbol, source=data.source,
            score=round(score, 1),
            total_bars=n, missing_bars=missing,
            anomaly_count=price_anomalies + volume_anomalies,
            gap_count=gaps, max_gap_days=max_gap,
            price_anomaly_count=price_anomalies,
            volume_anomaly_count=volume_anomalies,
            details=details,
        )

    def cross_validate(self, symbol: str, interval: KlineInterval = KlineInterval.DAY,
                        sources: Optional[List[str]] = None) -> CrossValidationResult:
        """
        多数据源交叉验证。

        Args:
            symbol: 品种代码
            interval: K线周期
            sources: 数据源列表 (默认使用所有)
        """
        all_sources = self._source_mgr.list_sources()
        if not all_sources:
            return CrossValidationResult(
                symbol=symbol, interval=interval.value,
                sources_available=[], correlation=0,
                price_deviation_pct=0, volume_deviation_pct=0,
                is_consistent=False, details=["No sources available"],
            )

        # 获取多个数据源的数据
        results = self._source_mgr.get_kline_multi_source(
            symbol=symbol, interval=interval
        )

        source_names = list(results.keys())
        if len(source_names) < 1:
            return CrossValidationResult(
                symbol=symbol, interval=interval.value,
                sources_available=[], correlation=0,
                price_deviation_pct=0, volume_deviation_pct=0,
                is_consistent=False, details=["No data available"],
            )

        if len(source_names) < 2:
            return CrossValidationResult(
                symbol=symbol, interval=interval.value,
                sources_available=source_names,
                correlation=1.0, price_deviation_pct=0,
                volume_deviation_pct=0, is_consistent=True,
                details=["Only one source available"],
            )

        # 计算相关性
        closes: List[np.ndarray] = []
        for name in source_names:
            arr = np.array(results[name].close, dtype=float)
            if len(arr) > 0:
                closes.append(arr)

        details_list = []
        min_len = min(len(c) for c in closes) if closes else 0
        if min_len < 5:
            return CrossValidationResult(
                symbol=symbol, interval=interval.value,
                sources_available=source_names,
                correlation=0, price_deviation_pct=0,
                volume_deviation_pct=0, is_consistent=False,
                details=["Insufficient data for comparison"],
            )

        # 截取相同长度
        closes_aligned = [c[-min_len:] for c in closes]

        # 计算相关系数
        corr_matrix = np.corrcoef(closes_aligned)
        avg_corr = float(np.mean(corr_matrix[np.triu_indices_from(corr_matrix, k=1)])) if len(closes) > 1 else 1.0

        # 计算价格偏差
        price_deviations = []
        for i in range(len(closes_aligned)):
            for j in range(i+1, len(closes_aligned)):
                dev = np.mean(np.abs(closes_aligned[i] - closes_aligned[j]) / (closes_aligned[i] + 1e-10)) * 100
                price_deviations.append(dev)

        max_dev = max(price_deviations) if price_deviations else 0
        is_consistent = avg_corr > 0.95 and max_dev < 5.0

        details_list.append(f"数据源: {', '.join(source_names)}")
        details_list.append(f"相关系数: {avg_corr:.4f}")
        details_list.append(f"最大价格偏差: {max_dev:.2f}%")

        return CrossValidationResult(
            symbol=symbol, interval=interval.value,
            sources_available=source_names,
            correlation=round(avg_corr, 4),
            price_deviation_pct=round(max_dev, 2),
            volume_deviation_pct=0,
            is_consistent=is_consistent,
            details=details_list,
        )

    def cross_validate_all(self, symbols: List[str]) -> Dict[str, CrossValidationResult]:
        """批量交叉验证"""
        results = {}
        for sym in symbols:
            try:
                results[sym] = self.cross_validate(sym)
            except Exception as e:
                logger.warning(f"Cross-validate failed for {sym}: {e}")
        return results
