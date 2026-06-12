from typing import List
import numpy as np
from signals.base import Signal, Direction


class MatrixEngine:
    """楚风相关矩阵引擎 - 考虑信号一致性"""

    def calculate(self, signals: List[Signal]) -> float:
        if not signals:
            return 0.0

        scores = []
        for signal in signals:
            s = signal.score
            if signal.direction == Direction.SELL:
                s = -abs(s)
            elif signal.direction == Direction.BUY:
                s = abs(s)
            scores.append(s)

        if len(scores) < 2:
            return max(-10.0, min(10.0, scores[0]))

        arr = np.array(scores)
        mean_score = float(np.mean(arr))

        if np.std(arr) < 1e-10:
            consistency = 1.0
        else:
            n = len(arr)
            if n < 2:
                consistency = 1.0
            else:
                corr_matrix = np.corrcoef(arr, np.ones(n))
                avg_corr = corr_matrix[0, 1] if not np.isnan(corr_matrix[0, 1]) else 0.0
                consistency = max(0.0, min(1.0, (avg_corr + 1.0) / 2.0))

        result = mean_score * (0.6 + 0.4 * consistency)
        return max(-10.0, min(10.0, result))
