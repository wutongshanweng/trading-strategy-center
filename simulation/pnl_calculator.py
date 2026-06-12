from typing import List
import numpy as np
from simulation.position_manager import Position


class PnLCalculator:
    def __init__(self):
        self.total_pnl = 0.0
        self._realized_pnl = 0.0
        self._closed_trades: list = []

    def update(self, positions: List[Position], current_price: float = None) -> float:
        total = 0.0
        for pos in positions:
            if current_price is not None:
                pos.current_price = current_price
            total += pos.pnl
        return total

    def close_trade(self, pos: Position, exit_price: float):
        pnl = (exit_price - pos.entry_price) * pos.quantity if pos.direction.value == "BUY" \
            else (pos.entry_price - exit_price) * pos.quantity
        self._realized_pnl += pnl
        self.total_pnl += pnl
        self._closed_trades.append({
            "symbol": pos.symbol, "direction": pos.direction.value,
            "entry": pos.entry_price, "exit": exit_price,
            "quantity": pos.quantity, "pnl": pnl,
        })

    def summary(self) -> dict:
        pnls = [t["pnl"] for t in self._closed_trades]
        return {
            "total_pnl": round(self.total_pnl, 2),
            "realized_pnl": round(self._realized_pnl, 2),
            "trade_count": len(self._closed_trades),
            "win_rate": round(sum(1 for p in pnls if p > 0) / len(pnls), 4) if pnls else 0.0,
            "avg_pnl": round(np.mean(pnls), 2) if pnls else 0.0,
            "max_pnl": round(max(pnls), 2) if pnls else 0.0,
            "min_pnl": round(min(pnls), 2) if pnls else 0.0,
        }
