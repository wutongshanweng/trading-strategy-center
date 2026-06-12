from typing import List
import numpy as np
from simulation.position_manager import Position


def score_positions(positions: List[Position]) -> dict:
    if not positions:
        return {"total_pnl": 0.0, "avg_pnl_pct": 0.0, "win_rate": 0.0, "score": 0.0}
    pnls = [p.pnl for p in positions]
    pnl_pcts = [p.pnl_pct for p in positions]
    wins = sum(1 for p in pnls if p > 0)
    score = np.mean(pnl_pcts) * 100 - np.std(pnl_pcts) * 0.5 + (wins / len(pnls)) * 0.5
    return {
        "total_pnl": round(sum(pnls), 2),
        "avg_pnl_pct": round(float(np.mean(pnl_pcts)), 4),
        "win_rate": round(wins / len(pnls), 4),
        "score": round(float(score), 4),
    }
