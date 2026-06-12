from typing import List
from signals.base import Signal, Direction


class ScannerEngine:
    """听海阈值扫描引擎 - 过滤低于阈值的信号"""

    def __init__(self, threshold: float = 2.0):
        self.threshold = threshold

    def calculate(self, signals: List[Signal]) -> float:
        if not signals:
            return 0.0

        filtered = []
        for signal in signals:
            if abs(signal.score) >= self.threshold:
                filtered.append(signal)

        if not filtered:
            return 0.0

        total_score = 0.0
        total_weight = 0.0

        for signal in filtered:
            weight = abs(signal.confidence)
            s = signal.score
            if signal.direction == Direction.SELL:
                s = -abs(s)
            elif signal.direction == Direction.BUY:
                s = abs(s)

            total_score += s * weight
            total_weight += weight

        if total_weight < 1e-10:
            return 0.0

        return max(-10.0, min(10.0, total_score / total_weight))
