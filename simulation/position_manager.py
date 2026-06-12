from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime
from signals.base import Direction


@dataclass
class Position:
    symbol: str
    direction: Direction
    quantity: int
    entry_price: float
    current_price: float
    stop_loss: float = 0.0
    take_profit: float = 0.0
    opened_at: datetime = None
    status: str = "OPEN"

    def __post_init__(self):
        if self.opened_at is None:
            self.opened_at = datetime.utcnow()

    @property
    def pnl(self) -> float:
        if self.direction == Direction.BUY:
            return (self.current_price - self.entry_price) * self.quantity
        return (self.entry_price - self.current_price) * self.quantity

    @property
    def pnl_pct(self) -> float:
        cost = self.entry_price * self.quantity
        return self.pnl / cost if cost > 0 else 0.0


class PositionManager:
    def __init__(self):
        self._positions: List[Position] = []

    def open(self, symbol: str, direction: Direction, quantity: int,
             price: float, stop_loss: float = 0.0, take_profit: float = 0.0) -> Optional[Position]:
        existing = [p for p in self._positions if p.symbol == symbol and p.status == "OPEN"]
        if existing and existing[0].direction == direction:
            return None  # already have position in same direction
        if existing and existing[0].direction != direction:
            self.close(symbol, price)  # close opposite first
        pos = Position(symbol=symbol, direction=direction, quantity=quantity,
                       entry_price=price, current_price=price,
                       stop_loss=stop_loss, take_profit=take_profit)
        self._positions.append(pos)
        return pos

    def close(self, symbol: str, price: float) -> Optional[Position]:
        for pos in self._positions:
            if pos.symbol == symbol and pos.status == "OPEN":
                pos.current_price = price
                pos.status = "CLOSED"
                return pos
        return None

    def update_prices(self, updates: dict):
        for pos in self._positions:
            if pos.status == "OPEN" and pos.symbol in updates:
                pos.current_price = updates[pos.symbol]

    def get(self, symbol: str) -> Optional[Position]:
        for pos in self._positions:
            if pos.symbol == symbol and pos.status == "OPEN":
                return pos
        return None

    def get_all(self) -> List[Position]:
        return [p for p in self._positions if p.status == "OPEN"]

    def position_count(self) -> int:
        return len(self.get_all())
