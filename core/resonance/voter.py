from typing import List
from signals.base import Signal, Direction


class VoterEngine:
    """观山加权投票引擎 - confidence加权投票"""

    def calculate(self, signals: List[Signal]) -> float:
        if not signals:
            return 0.0

        total_score = 0.0
        total_weight = 0.0

        for signal in signals:
            weight = abs(signal.confidence)
            score = signal.score
            if signal.direction == Direction.SELL:
                score = -abs(score)
            elif signal.direction == Direction.BUY:
                score = abs(score)

            total_score += score * weight
            total_weight += weight

        if total_weight < 1e-10:
            return 0.0

        return max(-10.0, min(10.0, total_score / total_weight))
