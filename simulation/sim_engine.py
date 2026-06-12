from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from loguru import logger

from signals.base import Signal, Direction
from simulation.position_manager import PositionManager
from simulation.pnl_calculator import PnLCalculator
from simulation.rule_engine import RuleEngine
from risk.risk_manager import RiskManager


@dataclass
class TradeResult:
    symbol: str
    direction: Direction
    entry_price: float
    quantity: int
    timestamp: datetime
    reason: str
    accepted: bool = True
    reject_reason: str = ""


class SimEngine:
    def __init__(self, initial_capital: float = 1_000_000.0):
        self.capital = initial_capital
        self.equity = initial_capital
        self.positions = PositionManager()
        self.pnl = PnLCalculator()
        self.rules = RuleEngine()
        self.risk = RiskManager()
        self._trade_log: List[TradeResult] = []
        self._lock = asyncio.Lock()

    async def execute_signal(self, signal: Signal) -> Optional[TradeResult]:
        async with self._lock:
            if not await self.rules.check(signal):
                return TradeResult(signal.symbol, signal.direction, 0.0, 0,
                                   datetime.utcnow(), "", False, "rule engine rejected")
            verdict = self.risk.check_signal(signal.symbol, signal.direction.value,
                                              signal, self.positions.get_all())
            if not verdict.allowed:
                return TradeResult(signal.symbol, signal.direction, 0.0, 0,
                                   datetime.utcnow(), "", False, verdict.reason)
            position = self.positions.open(signal.symbol, signal.direction,
                                           verdict.max_size, signal.price)
            if position is None:
                return TradeResult(signal.symbol, signal.direction, signal.price, 0,
                                   datetime.utcnow(), "", False, "position manager rejected")
            result = TradeResult(signal.symbol, signal.direction, signal.price,
                                 position.quantity, datetime.utcnow(), signal.reason)
            self._trade_log.append(result)
            self.equity = self.pnl.update(self.positions.get_all(), signal.price)
            logger.info(f"Executed {result.direction} {result.quantity} of {result.symbol} @ {result.entry_price}")
            return result

    async def close_position(self, symbol: str, price: float) -> Optional[TradeResult]:
        async with self._lock:
            pos = self.positions.close(symbol, price)
            if pos is None:
                return None
            self.equity = self.pnl.update(self.positions.get_all(), price)
            result = TradeResult(symbol, Direction.HOLD, price, 0, datetime.utcnow(), "manual close")
            self._trade_log.append(result)
            return result

    def get_portfolio_summary(self) -> dict:
        total_value = sum(p.quantity * p.current_price for p in self.positions.get_all())
        return {
            "capital": self.capital,
            "equity": self.equity,
            "position_value": total_value,
            "total_value": self.equity + total_value,
            "positions": len(self.positions.get_all()),
            "pnl": self.pnl.total_pnl,
            "trades": len(self._trade_log),
        }
