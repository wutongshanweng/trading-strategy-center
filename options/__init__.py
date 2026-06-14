"""期权专属层 — 定价 / 希腊字母 / 波动率 / 策略 / 风险 / 分析。

P0 范围(对齐《架构升级建议与策略模型规划.md》):
  - pricing:    BSM / Black76 / 二叉树
  - greeks:     解析希腊字母 + 组合级聚合
  - volatility: IV 反求 / 已实现波动率 / SVI 曲面
  - strategies: 期权策略(方向/卖波动率/买波动率/日历)
  - risk:       组合 Greeks 限额
  - analysis:   PCR / Max Pain
"""

__all__ = [
    "pricing",
    "greeks",
    "volatility",
    "strategies",
    "risk",
    "analysis",
]
