from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from simulation.position_manager import Position
from portfolio.capital_allocation import CapitalAllocation
from portfolio.correlation_matrix import CorrelationMatrix


class PortfolioManager:
    def __init__(self, initial_capital: float = 1_000_000.0):
        self.capital = initial_capital
        self.equity = initial_capital
        self.allocation = CapitalAllocation(initial_capital)
        self.correlation = CorrelationMatrix()

    def update_prices(self, price_dict: Dict[str, float]):
        for symbol, price in price_dict.items():
            self.correlation.add_price(symbol, price)

    def get_portfolio_stats(self, positions: List[Position]) -> Dict:
        pos_value = sum(p.quantity * p.current_price for p in positions)
        cash = self.equity - pos_value
        pnls = [p.pnl for p in positions]
        weights = {p.symbol: (p.quantity * p.current_price) / max(self.equity, 1) for p in positions}

        return {
            "total_value": round(self.equity, 2),
            "cash": round(cash, 2),
            "position_value": round(pos_value, 2),
            "position_count": len(positions),
            "exposure_pct": round(pos_value / max(self.equity, 1), 4),
            "weights": {k: round(v, 4) for k, v in weights.items()},
            "total_pnl": round(sum(pnls), 2),
            "diversification": round(1 - sum(w ** 2 for w in weights.values()), 4) if weights else 0.0,
        }

    def rebalance(self, positions: List[Position], target_weights: Dict[str, float]) -> List[Dict]:
        trades = []
        for symbol, target in target_weights.items():
            pos = next((p for p in positions if p.symbol == symbol), None)
            current_weight = (pos.quantity * pos.current_price) / max(self.equity, 1) if pos else 0.0
            diff = target - current_weight
            if abs(diff) > 0.01:
                value = diff * self.equity
                price = pos.current_price if pos else 0.0
                qty = int(abs(value) / price) if price > 0 else 0
                if qty > 0:
                    trades.append({"symbol": symbol, "direction": "BUY" if diff > 0 else "SELL", "quantity": qty})
        return trades
