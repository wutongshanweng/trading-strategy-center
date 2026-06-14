"""卖波动率策略:Short Straddle / Short Strangle / Iron Condor / Iron Butterfly。

适用于震荡/高 IV 环境,赚 theta 衰减。Iron 系列有限风险。
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
class ShortStraddleStrategy(BaseOptionStrategy):
    """卖出跨式:同时卖出平值 Call + Put。

    最大盈利 = 收到的总权利金;风险无限(双向)。
    盈亏平衡 = strike ± 总权利金。
    """

    strategy_name = "short_straddle"
    DEFAULT_PARAMS = {}

    def build(self, underlying: str, spot: float, expiry: datetime,
              call_premium: float, put_premium: float,
              strike: Optional[float] = None, quantity: int = 1,
              confidence: float = 0.5) -> OptionStrategySignal:
        if strike is None:
            strike = round(spot, 2)
        total_prem = call_premium + put_premium
        legs = [
            OptionLeg(underlying, OptionType.CALL, strike, expiry, Action.SELL, quantity, call_premium),
            OptionLeg(underlying, OptionType.PUT, strike, expiry, Action.SELL, quantity, put_premium),
        ]
        return OptionStrategySignal(
            strategy_name=self.strategy_name,
            underlying=underlying,
            direction="SHORT_VOL",
            legs=legs,
            confidence=confidence,
            score=confidence * 6,
            expected_max_profit=total_prem * quantity,
            expected_max_loss=None,
            breakeven_points=[strike - total_prem, strike + total_prem],
            target_iv_rank=0.7,
            notes=f"卖 ATM K={strike} Straddle 收 {total_prem:.2f}",
        )


@register
class ShortStrangleStrategy(BaseOptionStrategy):
    """卖出宽跨式:卖出虚值 Call + 虚值 Put,比跨式更宽容错区间。"""

    strategy_name = "short_strangle"
    DEFAULT_PARAMS = {"call_otm_pct": 0.04, "put_otm_pct": 0.04}

    def build(self, underlying: str, spot: float, expiry: datetime,
              call_premium: float, put_premium: float,
              call_strike: Optional[float] = None, put_strike: Optional[float] = None,
              quantity: int = 1, confidence: float = 0.5) -> OptionStrategySignal:
        if call_strike is None:
            call_strike = round(spot * (1 + self.params["call_otm_pct"]), 2)
        if put_strike is None:
            put_strike = round(spot * (1 - self.params["put_otm_pct"]), 2)
        total_prem = call_premium + put_premium
        legs = [
            OptionLeg(underlying, OptionType.CALL, call_strike, expiry, Action.SELL, quantity, call_premium),
            OptionLeg(underlying, OptionType.PUT, put_strike, expiry, Action.SELL, quantity, put_premium),
        ]
        return OptionStrategySignal(
            strategy_name=self.strategy_name,
            underlying=underlying,
            direction="SHORT_VOL",
            legs=legs,
            confidence=confidence,
            score=confidence * 6,
            expected_max_profit=total_prem * quantity,
            expected_max_loss=None,
            breakeven_points=[put_strike - total_prem, call_strike + total_prem],
            target_iv_rank=0.7,
            notes=f"卖 Strangle P={put_strike}/C={call_strike} 收 {total_prem:.2f}",
        )


@register
class IronCondorStrategy(BaseOptionStrategy):
    """铁鹰:卖近的宽跨式 + 买更远的 Call/Put 保护,有限风险有限收益。

    四腿:卖 OTM Put、买更低 Put、卖 OTM Call、买更高 Call。
    最大盈利 = 净收权利金;最大亏损 = 翼宽 - 净权利金。
    """

    strategy_name = "iron_condor"
    DEFAULT_PARAMS = {
        "short_put_otm": 0.03,
        "short_call_otm": 0.03,
        "wing_width_pct": 0.02,
    }

    def build(self, underlying: str, spot: float, expiry: datetime,
              short_put_prem: float, long_put_prem: float,
              short_call_prem: float, long_call_prem: float,
              quantity: int = 1, confidence: float = 0.55) -> OptionStrategySignal:
        p = self.params
        short_put_k = round(spot * (1 - p["short_put_otm"]), 2)
        long_put_k = round(spot * (1 - p["short_put_otm"] - p["wing_width_pct"]), 2)
        short_call_k = round(spot * (1 + p["short_call_otm"]), 2)
        long_call_k = round(spot * (1 + p["short_call_otm"] + p["wing_width_pct"]), 2)

        net_credit = (short_put_prem + short_call_prem) - (long_put_prem + long_call_prem)
        put_wing = short_put_k - long_put_k
        call_wing = long_call_k - short_call_k
        max_wing = max(put_wing, call_wing)
        max_loss = (max_wing - net_credit) * quantity

        legs = [
            OptionLeg(underlying, OptionType.PUT, short_put_k, expiry, Action.SELL, quantity, short_put_prem),
            OptionLeg(underlying, OptionType.PUT, long_put_k, expiry, Action.BUY, quantity, long_put_prem),
            OptionLeg(underlying, OptionType.CALL, short_call_k, expiry, Action.SELL, quantity, short_call_prem),
            OptionLeg(underlying, OptionType.CALL, long_call_k, expiry, Action.BUY, quantity, long_call_prem),
        ]
        return OptionStrategySignal(
            strategy_name=self.strategy_name,
            underlying=underlying,
            direction="SHORT_VOL",
            legs=legs,
            confidence=confidence,
            score=confidence * 7,
            expected_max_profit=net_credit * quantity,
            expected_max_loss=max_loss,
            breakeven_points=[short_put_k - net_credit, short_call_k + net_credit],
            target_iv_rank=0.6,
            notes=(f"Iron Condor P{long_put_k}/{short_put_k} "
                   f"C{short_call_k}/{long_call_k} 净收 {net_credit:.2f}"),
        )


@register
class IronButterflyStrategy(BaseOptionStrategy):
    """铁蝶:ATM 卖跨式 + 两翼买保护,比铁鹰收权利金更多但盈利区间更窄。"""

    strategy_name = "iron_butterfly"
    DEFAULT_PARAMS = {"wing_width_pct": 0.03}

    def build(self, underlying: str, spot: float, expiry: datetime,
              short_call_prem: float, short_put_prem: float,
              long_call_prem: float, long_put_prem: float,
              center_strike: Optional[float] = None,
              quantity: int = 1, confidence: float = 0.5) -> OptionStrategySignal:
        if center_strike is None:
            center_strike = round(spot, 2)
        wing = round(spot * self.params["wing_width_pct"], 2)
        long_put_k = center_strike - wing
        long_call_k = center_strike + wing

        net_credit = (short_call_prem + short_put_prem) - (long_call_prem + long_put_prem)
        max_loss = (wing - net_credit) * quantity

        legs = [
            OptionLeg(underlying, OptionType.CALL, center_strike, expiry, Action.SELL, quantity, short_call_prem),
            OptionLeg(underlying, OptionType.PUT, center_strike, expiry, Action.SELL, quantity, short_put_prem),
            OptionLeg(underlying, OptionType.CALL, long_call_k, expiry, Action.BUY, quantity, long_call_prem),
            OptionLeg(underlying, OptionType.PUT, long_put_k, expiry, Action.BUY, quantity, long_put_prem),
        ]
        return OptionStrategySignal(
            strategy_name=self.strategy_name,
            underlying=underlying,
            direction="SHORT_VOL",
            legs=legs,
            confidence=confidence,
            score=confidence * 6,
            expected_max_profit=net_credit * quantity,
            expected_max_loss=max_loss,
            breakeven_points=[center_strike - net_credit, center_strike + net_credit],
            target_iv_rank=0.65,
            notes=(f"Iron Butterfly center={center_strike} 翼±{wing} "
                   f"净收 {net_credit:.2f}"),
        )
