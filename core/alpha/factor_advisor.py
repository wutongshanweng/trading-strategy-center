"""
因子建议器 — 把因子分析结果翻译成可执行的交易建议。

用法:
    advisor = FactorAdvisor()
    advice = advisor.advise_from_report(symbol, report, combined_signal)
    print(advice.summary())
    # → "【RB2510】🟢 做多 置信度:中高 ..."

设计:
  方向     = 综合信号值 signal_value 的符号 (正=偏多, 负=偏空)
  置信度   = 综合 ICIR (越大越可靠)
  最终建议 = signal_value 与 ICIR 的组合判断 (见 advise() 决策规则)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import pandas as pd


@dataclass
class TradingAdvice:
    """交易建议。"""
    symbol: str                       # 标的
    action: str                       # BUY / SELL / HOLD / WAIT
    action_cn: str                    # 做多 / 做空 / 观望 / 谨慎
    confidence: str                   # 高 / 中高 / 中 / 低 / 极低
    confidence_score: float           # 0~1
    signal_value: float               # 综合信号值 (正=看多, 负=看空)
    reason: str                       # 一句话理由
    details: Dict = field(default_factory=dict)
    risk_note: str = ""               # 风险提示

    def summary(self) -> str:
        icon = {"BUY": "🟢", "SELL": "🔴", "HOLD": "⚪", "WAIT": "🟡"}.get(self.action, "⚪")
        s = (f"【{self.symbol}】{icon} {self.action_cn} 置信度:{self.confidence} "
             f"综合信号:{self.signal_value:+.4f}\n  理由: {self.reason}")
        if self.risk_note:
            s += f"\n  {self.risk_note}"
        return s

    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol, "action": self.action, "action_cn": self.action_cn,
            "confidence": self.confidence, "confidence_score": self.confidence_score,
            "signal_value": self.signal_value, "reason": self.reason,
            "risk_note": self.risk_note, "details": self.details,
        }


class FactorAdvisor:
    """因子建议器: 因子分析结果 → 可执行交易建议。"""

    def advise(
        self,
        symbol: str,
        combined_signal: pd.Series,
        icir: float,
        factor_count: int,
        top_factors: List[Dict],
        health_distribution: Dict,
    ) -> TradingAdvice:
        """生成交易建议。

        决策规则:
          signal > 0.15 且 ICIR > 0.5  → BUY  (做多)
          signal < -0.15 且 ICIR > 0.5 → SELL (做空)
          |signal| < 0.05 或 ICIR < 0.1 → HOLD (信号太弱/不可靠, 不交易)
          ICIR < 0.3                    → WAIT (小仓位试探)
          其他                           → WAIT (强度不足)

        置信度: ICIR >1.0 高 / >0.5 中高 / >0.2 中 / >0.0 低 / 否则 极低
        """
        signal_val = float(combined_signal.mean()) if len(combined_signal) else 0.0
        if not _finite(signal_val):
            signal_val = 0.0
        icir = icir if _finite(icir) else 0.0

        if signal_val > 0.15 and icir > 0.5:
            action, action_cn = "BUY", "做多"
            reason = f"综合信号 {signal_val:+.2f} (正向偏多), ICIR={icir:.2f} (高置信度)"
        elif signal_val < -0.15 and icir > 0.5:
            action, action_cn = "SELL", "做空"
            reason = f"综合信号 {signal_val:+.2f} (负向偏空), ICIR={icir:.2f} (高置信度)"
        elif abs(signal_val) < 0.05 or icir < 0.1:
            action, action_cn = "HOLD", "观望"
            reason = (f"综合信号 {signal_val:+.2f} 接近零 或 ICIR={icir:.2f} 过低, "
                      f"方向不明确, 暂不建议交易")
        elif icir < 0.3:
            action, action_cn = "WAIT", "谨慎"
            reason = f"综合信号 {signal_val:+.2f}, 但 ICIR={icir:.2f} 偏低, 建议小仓位试探或等信号强化"
        else:
            action, action_cn = "WAIT", "谨慎"
            reason = f"信号方向存在但强度不足 (signal={signal_val:+.2f}, ICIR={icir:.2f})"

        if icir > 1.0:
            conf = "高"
        elif icir > 0.5:
            conf = "中高"
        elif icir > 0.2:
            conf = "中"
        elif icir > 0.0:
            conf = "低"
        else:
            conf = "极低"

        health_ok = health_distribution.get("healthy", 0)
        health_total = sum(health_distribution.values())
        if health_total and health_ok / max(health_total, 1) < 0.3:
            risk = "⚠️ 大部分因子处于非健康状态, 建议谨慎对待当前信号"
        elif factor_count < 3:
            risk = "参与信号因子不足(<3), 信号可能不稳定"
        else:
            risk = ""

        return TradingAdvice(
            symbol=symbol, action=action, action_cn=action_cn,
            confidence=conf, confidence_score=round(min(abs(icir), 1.0), 4),
            signal_value=round(signal_val, 4), reason=reason,
            details={
                "icir": round(icir, 4), "factor_count": factor_count,
                "top_factors": top_factors[:5], "health": health_distribution,
            },
            risk_note=risk,
        )

    def advise_from_report(
        self,
        symbol: str,
        report,                       # FactorResearchReport
        combined_signal: pd.Series,
    ) -> TradingAdvice:
        """从 FactorResearchReport 生成建议。"""
        return self.advise(
            symbol=symbol,
            combined_signal=combined_signal,
            icir=getattr(report, "recommended_icir", 0.0),
            factor_count=len(getattr(report, "recommended", [])),
            top_factors=[
                {"name": f.name, "ic": f.ic_mean, "health": f.health}
                for f in getattr(report, "top_factors", [])[:5]
            ],
            health_distribution={
                "healthy": getattr(report, "healthy_count", 0),
                "warning": getattr(report, "warning_count", 0),
                "decayed": getattr(report, "decayed_count", 0),
            },
        )


def _finite(v) -> bool:
    try:
        import math
        return math.isfinite(float(v))
    except (TypeError, ValueError):
        return False
