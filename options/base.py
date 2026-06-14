"""期权策略基础数据结构与基类。

沿用现有 signals/base.py 的设计风格(dataclass 信号 + 类基类),
但期权策略产出的是多腿组合信号 OptionStrategySignal,而非单点 Signal。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional


class OptionType(str, Enum):
    CALL = "C"
    PUT = "P"


class Action(str, Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class OptionLeg:
    """期权组合中的一条腿。"""
    underlying: str
    option_type: OptionType
    strike: float
    expiry: datetime
    action: Action
    quantity: int = 1
    premium: Optional[float] = None      # 权利金(开仓时)
    iv: Optional[float] = None           # 该腿隐含波动率(可选)

    @property
    def signed_qty(self) -> int:
        return self.quantity if self.action == Action.BUY else -self.quantity


@dataclass
class FuturesLeg:
    """搭配期货腿(用于 covered call / Delta 对冲等)。"""
    underlying: str
    action: Action
    quantity: int
    entry_price: Optional[float] = None

    @property
    def signed_qty(self) -> int:
        return self.quantity if self.action == Action.BUY else -self.quantity


Direction = Literal[
    "LONG_VOL", "SHORT_VOL", "DIRECTIONAL_BULL",
    "DIRECTIONAL_BEAR", "NEUTRAL", "HOLD",
]


@dataclass
class OptionStrategySignal:
    """期权策略输出:一个完整的多腿组合 + 风险刻画。"""
    strategy_name: str
    underlying: str
    direction: Direction
    legs: List[OptionLeg]
    futures_legs: List[FuturesLeg] = field(default_factory=list)
    confidence: float = 0.0
    score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    expected_max_profit: Optional[float] = None
    expected_max_loss: Optional[float] = None
    breakeven_points: List[float] = field(default_factory=list)
    target_iv_rank: Optional[float] = None
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def net_premium(self) -> float:
        """净权利金:卖方收入为正,买方支出为负。"""
        total = 0.0
        for leg in self.legs:
            if leg.premium is None:
                continue
            sign = -1 if leg.action == Action.BUY else 1
            total += sign * leg.premium * leg.quantity
        return total


class BaseOptionStrategy:
    """期权策略基类(不强制 ABC,允许灵活实现)。"""

    strategy_name: str = "BaseOption"
    DEFAULT_PARAMS: Dict[str, Any] = {}

    def __init__(self, params: Optional[Dict] = None):
        self.params: Dict[str, Any] = {**self.DEFAULT_PARAMS, **(params or {})}

    def build(self, **kwargs) -> OptionStrategySignal:
        raise NotImplementedError

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.strategy_name}>"
