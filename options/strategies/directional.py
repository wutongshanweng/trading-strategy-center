"""方向性期权策略:Long Call / Long Put / Covered Call / Protective Put。"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from options.base import (
    Action,
    BaseOptionStrategy,
    FuturesLeg,
    OptionLeg,
    OptionStrategySignal,
    OptionType,
)
from options.registry import register


@register
class LongCallStrategy(BaseOptionStrategy):
    """单腿买入(虚值/平值)看涨。

    最大亏损 = 权利金;最大盈利无限;盈亏平衡 = strike + premium。
    """

    strategy_name = "long_call"
    DEFAULT_PARAMS = {"otm_pct": 0.02}

    def build(self, underlying: str, spot: float, expiry: datetime,
              premium: float, strike: Optional[float] = None,
              quantity: int = 1, confidence: float = 0.6) -> OptionStrategySignal:
        if strike is None:
            strike = round(spot * (1 + self.params["otm_pct"]), 2)
        leg = OptionLeg(underlying, OptionType.CALL, strike, expiry,
                        Action.BUY, quantity, premium)
        return OptionStrategySignal(
            strategy_name=self.strategy_name,
            underlying=underlying,
            direction="DIRECTIONAL_BULL",
            legs=[leg],
            confidence=confidence,
            score=confidence * 6,
            expected_max_loss=premium * quantity,
            expected_max_profit=None,
            breakeven_points=[strike + premium],
            notes=f"买 K={strike} Call @ {premium:.2f}",
        )


@register
class LongPutStrategy(BaseOptionStrategy):
    """单腿买入(虚值/平值)看跌。

    最大亏损 = 权利金;最大盈利 = strike - premium(标的归零);
    盈亏平衡 = strike - premium。
    """

    strategy_name = "long_put"
    DEFAULT_PARAMS = {"otm_pct": 0.02}

    def build(self, underlying: str, spot: float, expiry: datetime,
              premium: float, strike: Optional[float] = None,
              quantity: int = 1, confidence: float = 0.6) -> OptionStrategySignal:
        if strike is None:
            strike = round(spot * (1 - self.params["otm_pct"]), 2)
        leg = OptionLeg(underlying, OptionType.PUT, strike, expiry,
                        Action.BUY, quantity, premium)
        return OptionStrategySignal(
            strategy_name=self.strategy_name,
            underlying=underlying,
            direction="DIRECTIONAL_BEAR",
            legs=[leg],
            confidence=confidence,
            score=confidence * 6,
            expected_max_loss=premium * quantity,
            expected_max_profit=(strike - premium) * quantity,
            breakeven_points=[strike - premium],
            notes=f"买 K={strike} Put @ {premium:.2f}",
        )


@register
class CoveredCallStrategy(BaseOptionStrategy):
    """备兑看涨:持有标的(期货)+ 卖出虚值 Call,赚 theta。

    收益 = 卖 Call 权利金 + 标的上涨至 strike 的部分;
    风险 = 标的下跌(被权利金部分对冲)。
    """

    strategy_name = "covered_call"
    DEFAULT_PARAMS = {"otm_pct": 0.03}

    def build(self, underlying: str, spot: float, expiry: datetime,
              premium: float, strike: Optional[float] = None,
              quantity: int = 1, entry_price: Optional[float] = None,
              confidence: float = 0.55) -> OptionStrategySignal:
        if strike is None:
            strike = round(spot * (1 + self.params["otm_pct"]), 2)
        if entry_price is None:
            entry_price = spot
        call = OptionLeg(underlying, OptionType.CALL, strike, expiry,
                         Action.SELL, quantity, premium)
        fut = FuturesLeg(underlying, Action.BUY, quantity, entry_price)
        max_profit = (strike - entry_price + premium) * quantity
        return OptionStrategySignal(
            strategy_name=self.strategy_name,
            underlying=underlying,
            direction="NEUTRAL",
            legs=[call],
            futures_legs=[fut],
            confidence=confidence,
            score=confidence * 5,
            expected_max_profit=max_profit,
            expected_max_loss=None,  # 标的下跌风险敞口
            breakeven_points=[entry_price - premium],
            notes=f"持标的 @ {entry_price:.2f} + 卖 K={strike} Call @ {premium:.2f}",
        )


@register
class ProtectivePutStrategy(BaseOptionStrategy):
    """保护性看跌:持有标的 + 买入虚值 Put 做保险。

    最大亏损 = entry - strike + premium;最大盈利无限。
    """

    strategy_name = "protective_put"
    DEFAULT_PARAMS = {"otm_pct": 0.03}

    def build(self, underlying: str, spot: float, expiry: datetime,
              premium: float, strike: Optional[float] = None,
              quantity: int = 1, entry_price: Optional[float] = None,
              confidence: float = 0.5) -> OptionStrategySignal:
        if strike is None:
            strike = round(spot * (1 - self.params["otm_pct"]), 2)
        if entry_price is None:
            entry_price = spot
        put = OptionLeg(underlying, OptionType.PUT, strike, expiry,
                        Action.BUY, quantity, premium)
        fut = FuturesLeg(underlying, Action.BUY, quantity, entry_price)
        max_loss = (entry_price - strike + premium) * quantity
        return OptionStrategySignal(
            strategy_name=self.strategy_name,
            underlying=underlying,
            direction="DIRECTIONAL_BULL",
            legs=[put],
            futures_legs=[fut],
            confidence=confidence,
            score=confidence * 5,
            expected_max_profit=None,
            expected_max_loss=max_loss,
            breakeven_points=[entry_price + premium],
            notes=f"持标的 @ {entry_price:.2f} + 买 K={strike} Put @ {premium:.2f}",
        )
