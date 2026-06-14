"""期限结构策略:Calendar Spread(日历价差)。

卖近月 + 买远月同行权价期权,赚近月更快的 theta 衰减 + 远月 vega。
中性偏好:标的到期时停在行权价附近收益最大。
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
class CalendarSpreadStrategy(BaseOptionStrategy):
    """日历价差:卖近月、买远月,同行权价同类型。

    净支出 = 远月权利金 - 近月权利金(通常为正,即 debit)。
    最大亏损 ≈ 净支出;最大盈利在近月到期、标的贴近行权价时取得(无解析闭式,留空)。
    """

    strategy_name = "calendar_spread"
    DEFAULT_PARAMS = {"option_type": "C"}

    def build(self, underlying: str, spot: float,
              near_expiry: datetime, far_expiry: datetime,
              near_premium: float, far_premium: float,
              strike: Optional[float] = None, quantity: int = 1,
              option_type: Optional[str] = None,
              confidence: float = 0.5) -> OptionStrategySignal:
        if strike is None:
            strike = round(spot, 2)
        opt = OptionType(option_type or self.params["option_type"])
        net_debit = (far_premium - near_premium) * quantity
        legs = [
            OptionLeg(underlying, opt, strike, near_expiry, Action.SELL, quantity, near_premium),
            OptionLeg(underlying, opt, strike, far_expiry, Action.BUY, quantity, far_premium),
        ]
        return OptionStrategySignal(
            strategy_name=self.strategy_name,
            underlying=underlying,
            direction="NEUTRAL",
            legs=legs,
            confidence=confidence,
            score=confidence * 6,
            expected_max_profit=None,
            expected_max_loss=net_debit if net_debit > 0 else None,
            breakeven_points=[],
            target_iv_rank=0.4,
            notes=f"日历 {opt.value} K={strike} 卖近买远 净付 {net_debit:.2f}",
        )
