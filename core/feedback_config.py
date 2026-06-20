"""反馈闭环参数配置。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FeedbackConfig:
    """反馈闭环阈值配置。"""
    retire_sharpe: float = -0.5        # 夏普低于此值 → 标记下线
    retire_min_trades: int = 10        # 至少这么多交易才据夏普判定下线
    star_sharpe: float = 1.0           # 夏普高于此值 → 标记明星策略
    deactivate_on_retire: bool = True  # 下线时是否在目录里置 is_active=False
    retrain_on_decay: bool = False     # 表现退化时是否触发 ML 重训 (默认关, 避免误触发重训风暴)
