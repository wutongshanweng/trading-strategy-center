from dataclasses import dataclass
from typing import List, Optional
from signals.base import Signal, Direction
from simulation.position_manager import Position
from core.config.settings import get_settings


@dataclass
class RiskVerdict:
    allowed: bool
    reason: str = ""
    max_size: int = 0
    suggested_sl: float = 0.0
    suggested_tp: float = 0.0


class RiskManager:
    def __init__(self):
        self.settings = get_settings()

    def check_signal(self, symbol: str, direction: str, signal: Signal,
                     positions: List[Position]) -> RiskVerdict:
        pos_for_symbol = [p for p in positions if p.symbol == symbol]

        if pos_for_symbol:
            existing = pos_for_symbol[0]
            if existing.direction.value == direction:
                return RiskVerdict(False, "position already exists in same direction")
            if signal.confidence < 0.4:
                return RiskVerdict(False, "confidence too low to reverse")

        total_positions = len(positions)
        if total_positions >= 10:
            return RiskVerdict(False, f"max positions (10) reached")

        pos_value = sum(p.quantity * p.current_price for p in positions)
        if pos_value > self.settings.max_position_size * 10000:
            return RiskVerdict(False, "position value limit exceeded")

        atr = signal.extra.get("atr", signal.price * 0.02) if hasattr(signal, "extra") else signal.price * 0.02
        size = max(1, int(self.settings.max_position_size / max(1, total_positions + 1)))

        suggested_sl = signal.price * (1 - 0.02) if direction == "BUY" else signal.price * (1 + 0.02)
        suggested_tp = signal.price * (1 + 0.04) if direction == "BUY" else signal.price * (1 - 0.04)

        return RiskVerdict(True, "", size, suggested_sl, suggested_tp)
