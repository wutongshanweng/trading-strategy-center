"""
期限结构套利信号 — 利用 IV 期限结构异常偏离产生交易信号。

信号类型:
  1. IV_SKEW: 偏度极端 → 反转信号
  2. TERM_STRUCTURE: 近远月 IV 差极端 → 日历价差信号
  3. SURFACE_ARB: 曲面局部异常 → 蝶式/鹰式套利信号

用法:
    arb = TermArbitrageSignals()
    signals = arb.compute(surface=vol_surface, spot=3800)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np


@dataclass
class TermArbSignal:
    signal_type: str             # IV_SKEW / TERM_STRUCTURE / SURFACE_ARB
    direction: str               # BULLISH / BEARISH / NEUTRAL
    score: float                 # 0~1 信号强度
    confidence: float            # 0~1 置信度
    reason: str
    suggested_strategy: str = ""
    metadata: Dict = field(default_factory=dict)


class TermArbitrageSignals:
    """期限结构套利信号 — 检测 skew / 期限结构 / 曲面局部三类异常。"""

    def __init__(self, skew_threshold: float = 0.15, term_zscore_threshold: float = 2.0):
        self.skew_threshold = skew_threshold
        self.term_zscore_threshold = term_zscore_threshold

    def compute(self, surface, spot: float,
                history: Optional[Dict] = None) -> List[TermArbSignal]:
        """计算所有期限结构套利信号。"""
        signals: List[TermArbSignal] = []
        if (s := self._check_skew_extreme(surface, spot)):
            signals.append(s)
        if (s := self._check_term_structure(surface, spot, history)):
            signals.append(s)
        signals.extend(self._check_surface_arb(surface, spot))
        return signals

    def _check_skew_extreme(self, surface, spot) -> Optional[TermArbSignal]:
        sorted_T = sorted(surface.slices.keys())
        if not sorted_T:
            return None
        near_T = sorted_T[0]
        skew = surface.get_skew(near_T)
        if skew > self.skew_threshold:
            return TermArbSignal(
                "IV_SKEW", "BULLISH", min(abs(skew) * 2, 1.0), 0.6,
                f"Put 溢价极端 (skew={skew:.3f}), 市场过度恐惧, 预期反弹",
                "bull_call_spread", {"skew": skew, "T": near_T})
        if skew < -self.skew_threshold:
            return TermArbSignal(
                "IV_SKEW", "BEARISH", min(abs(skew) * 2, 1.0), 0.6,
                f"Call 溢价极端 (skew={skew:.3f}), 市场过度贪婪, 警惕回调",
                "bear_put_spread", {"skew": skew, "T": near_T})
        return None

    def _check_term_structure(self, surface, spot, history) -> Optional[TermArbSignal]:
        if len(surface.slices) < 2:
            return None
        sorted_T = sorted(surface.slices.keys())
        near, far = surface.slices[sorted_T[0]], surface.slices[sorted_T[-1]]
        near_iv = surface.get_iv(spot, near.T)
        far_iv = surface.get_iv(spot, far.T)
        if near_iv is None or far_iv is None:
            return None
        spread = far_iv - near_iv  # 正 = contango (远月更贵)

        if history and "term_spread_hist" in history:
            hist = np.array(history["term_spread_hist"])
            z = (spread - hist.mean()) / (hist.std() + 1e-10)
            if abs(z) > self.term_zscore_threshold:
                direction = "BEARISH" if spread > hist.mean() else "BULLISH"
                return TermArbSignal(
                    "TERM_STRUCTURE", direction, min(abs(z) / 5, 1.0), 0.7,
                    f"期限结构扭曲 (z-score={z:.1f}), {near.T:.2f}y vs {far.T:.2f}y",
                    "calendar_spread", {"spread": spread, "zscore": z})

        if spread > 0.05:
            return TermArbSignal(
                "TERM_STRUCTURE", "BEARISH", 0.4, 0.4,
                f"期限结构陡峭 contango (spread={spread:.2%}), 远月溢价高",
                "calendar_spread", {"spread": spread})
        if spread < -0.05:
            return TermArbSignal(
                "TERM_STRUCTURE", "BULLISH", 0.4, 0.4,
                f"期限结构 backwardation (spread={spread:.2%}), 近月恐慌",
                "calendar_spread", {"spread": spread})
        return None

    def _check_surface_arb(self, surface, spot) -> List[TermArbSignal]:
        """检测曲面局部异常 (蝶式套利机会)。"""
        signals = []
        for T, s in surface.slices.items():
            if len(s.ivs) < 3:
                continue
            for i in range(1, len(s.ivs) - 1):
                expected_mid = (s.ivs[i - 1] + s.ivs[i + 1]) / 2
                deviation = abs(s.ivs[i] - expected_mid)
                if deviation > 0.03:
                    is_convex = s.ivs[i] > expected_mid
                    signals.append(TermArbSignal(
                        "SURFACE_ARB",
                        "BEARISH" if is_convex else "BULLISH",
                        min(deviation * 10, 0.8), 0.5,
                        f"K={s.strikes[i]} IV 异常{'凸起' if is_convex else '凹陷'} ({deviation:.1%})",
                        "iron_condor" if is_convex else "long_butterfly",
                        {"T": T, "strike": float(s.strikes[i]), "deviation": deviation}))
                    break
        return signals
