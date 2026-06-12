from typing import Optional
from simulation.position_manager import Position


def calculate_kelly(wins: int, total: int, avg_win: float, avg_loss: float) -> float:
    if total == 0 or avg_loss == 0:
        return 0.0
    win_rate = wins / total
    loss_rate = 1 - win_rate
    b = avg_win / abs(avg_loss) if avg_loss != 0 else 0
    kelly = (b * win_rate - loss_rate) / b if b > 0 else 0
    return max(0.0, min(kelly, 0.25))


def calculate_position_size(capital: float, price: float, risk_pct: float = 0.02,
                             kelly_pct: float = 0.5) -> int:
    risk_amount = capital * risk_pct
    size = risk_amount / (price * kelly_pct)
    return max(1, int(size))
