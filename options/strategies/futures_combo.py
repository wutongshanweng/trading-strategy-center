"""
期权-期货联合策略 — 期货定方向, 期权定执行结构。

策略类型: covered_call / long_call / protective_put / cash_secured_put /
          long_put / protective_call / futures_only / hold

用法:
    combo = FuturesOptionsComboSignals()
    sig = combo.combine(futures_direction="BUY", futures_confidence=0.7,
                        iv_rank=85, skew=0.02, spot=3800)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ComboSignal:
    """期货-期权联合信号。"""
    strategy_name: str
    futures_direction: str          # LONG / SHORT / FLAT
    options_leg: str                # 期权腿描述
    adjusted_confidence: float
    adjusted_direction: str
    reason: str
    entry_conditions: Dict = field(default_factory=dict)
    risk_notes: str = ""


class FuturesOptionsComboSignals:
    """期货-期权联合策略信号 — 据期货信号 + 期权市场状态推荐联合策略。"""

    def combine(
        self,
        futures_direction: str,        # BUY / SELL / HOLD
        futures_confidence: float,     # 0~1
        iv_rank: float,                # 0~100
        skew: float,
        spot: float,
        term_structure: Optional[str] = None,
        options_available: bool = True,
    ) -> ComboSignal:
        """综合期货和期权信号, 输出联合策略。"""
        if futures_direction == "HOLD" or futures_confidence < 0.3:
            return ComboSignal(
                "hold", "FLAT", "none", 0.0, "HOLD", "期货信号不足, 不操作")
        if not options_available:
            return ComboSignal(
                "futures_only",
                "LONG" if futures_direction == "BUY" else "SHORT", "none",
                futures_confidence, futures_direction,
                f"无期权市场, 直接{'做多' if futures_direction == 'BUY' else '做空'}期货")
        return self._decide_strategy(
            futures_direction, futures_confidence, iv_rank, skew, spot, term_structure)

    def _decide_strategy(self, direction, confidence, iv_rank, skew,
                         spot, term_structure) -> ComboSignal:
        if direction == "BUY":
            if iv_rank > 70:
                otm = 0.03 if iv_rank > 85 else 0.05
                return ComboSignal(
                    "covered_call", "LONG", f"SELL OTM Call (+{otm*100:.0f}%)",
                    confidence * 0.9, "BULLISH",
                    f"IV Rank={iv_rank:.0f} 偏高, 卖Call收高权利金, 持仓增厚收益",
                    risk_notes="期货下跌风险未被对冲")
            if iv_rank < 30:
                return ComboSignal(
                    "long_call", "FLAT", "BUY ATM Call", confidence * 0.85, "BULLISH",
                    f"IV Rank={iv_rank:.0f} 偏低, 期权便宜, 用Call替代期货节省保证金",
                    risk_notes="时间价值衰减, 需方向性行情配合")
            if skew < -0.08:
                return ComboSignal(
                    "protective_put", "LONG", f"BUY OTM Put (skew={skew:.2f})",
                    confidence * 0.8, "BULLISH (protected)",
                    f"Skew={skew:.2f} 显示市场过度乐观, 买Put对冲回调风险",
                    risk_notes="保护成本 = 权利金")
            return ComboSignal(
                "futures_only", "LONG", "none", confidence, "BULLISH",
                "期权市场无异常信号, 直接做多期货")
        # SELL (对称)
        if iv_rank > 70:
            return ComboSignal(
                "cash_secured_put", "SHORT", "SELL OTM Put", confidence * 0.9, "BEARISH",
                f"IV Rank={iv_rank:.0f} 偏高, 卖Put收权利金")
        if iv_rank < 30:
            return ComboSignal(
                "long_put", "FLAT", "BUY ATM Put", confidence * 0.85, "BEARISH",
                f"IV Rank={iv_rank:.0f} 偏低, 期权便宜, 用Put替代期货")
        if skew > 0.08:
            return ComboSignal(
                "protective_call", "SHORT", "BUY OTM Call", confidence * 0.8,
                "BEARISH (protected)",
                f"Skew={skew:.2f} 显示市场恐慌, 买Call对冲反弹风险")
        return ComboSignal(
            "futures_only", "SHORT", "none", confidence, "BEARISH",
            "期权市场无异常信号, 直接做空期货")

    def compute_from_signals(self, futures_signal, options_signals: List) -> List[ComboSignal]:
        """从现有信号系统输入 (futures_signal + options 信号列表)。"""
        fd = getattr(futures_signal, "direction", "HOLD")
        fd = getattr(fd, "value", fd)  # Direction 枚举 → str
        fc = getattr(futures_signal, "confidence", 0.5)
        iv_rank, skew = 50.0, 0.0
        for sig in options_signals:
            st = getattr(sig, "signal_type", "")
            if st == "IV_RANK":
                iv_rank = getattr(sig, "value", 50)
            elif st == "SKEW":
                skew = getattr(sig, "value", 0.0)
        norm = ("BUY" if fd in ("BUY", "LONG") else
                "SELL" if fd in ("SELL", "SHORT") else "HOLD")
        return [self.combine(norm, fc, iv_rank, skew, spot=0)]
