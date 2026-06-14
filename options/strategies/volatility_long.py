"""买波动率策略:Long Straddle / Long Strangle。

适用于预期大波动但方向不明(低 IV 进场),赚 gamma/vega。
最大亏损 = 付出的总权利金,最大盈利方向无限。
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from options.base import (
    Action,
    BaseOptionStrategy,
    OptionLeg,
    OptionStrategySignal,
    OptionType,
)
from options.registry import register


@register
class LongStraddleStrategy(BaseOptionStrategy):
    """买入跨式:同时买入平值 Call + Put。"""

    strategy_name = "long_straddle"
    DEFAULT_PARAMS = {}

    def build(self, underlying: str, spot: float, expiry: datetime,
              call_premium: float, put_premium: float,
              strike: Optional[float] = None, quantity: int = 1,
              confidence: float = 0.5) -> OptionStrategySignal:
        if strike is None:
            strike = round(spot, 2)
        total_cost = call_premium + put_premium
        legs = [
            OptionLeg(underlying, OptionType.CALL, strike, expiry, Action.BUY, quantity, call_premium),
            OptionLeg(underlying, OptionType.PUT, strike, expiry, Action.BUY, quantity, put_premium),
        ]
        return OptionStrategySignal(
            strategy_name=self.strategy_name,
            underlying=underlying,
            direction="LONG_VOL",
            legs=legs,
            confidence=confidence,
            score=confidence * 6,
            expected_max_profit=None,
            expected_max_loss=total_cost * quantity,
            breakeven_points=[strike - total_cost, strike + total_cost],
            target_iv_rank=0.2,
            notes=f"买 ATM K={strike} Straddle 付 {total_cost:.2f}",
        )


@register
class LongStrangleStrategy(BaseOptionStrategy):
    """买入宽跨式:买虚值 Call + 虚值 Put,成本更低但需更大波动。"""

    strategy_name = "long_strangle"
    DEFAULT_PARAMS = {"call_otm_pct": 0.04, "put_otm_pct": 0.04}

    def build(self, underlying: str, spot: float, expiry: datetime,
              call_premium: float, put_premium: float,
              call_strike: Optional[float] = None, put_strike: Optional[float] = None,
              quantity: int = 1, confidence: float = 0.5) -> OptionStrategySignal:
        if call_strike is None:
            call_strike = round(spot * (1 + self.params["call_otm_pct"]), 2)
        if put_strike is None:
            put_strike = round(spot * (1 - self.params["put_otm_pct"]), 2)
        total_cost = call_premium + put_premium
        legs = [
            OptionLeg(underlying, OptionType.CALL, call_strike, expiry, Action.BUY, quantity, call_premium),
            OptionLeg(underlying, OptionType.PUT, put_strike, expiry, Action.BUY, quantity, put_premium),
        ]
        return OptionStrategySignal(
            strategy_name=self.strategy_name,
            underlying=underlying,
            direction="LONG_VOL",
            legs=legs,
            confidence=confidence,
            score=confidence * 6,
            expected_max_profit=None,
            expected_max_loss=total_cost * quantity,
            breakeven_points=[put_strike - total_cost, call_strike + total_cost],
            target_iv_rank=0.2,
            notes=f"买 Strangle P={put_strike}/C={call_strike} 付 {total_cost:.2f}",
        )
