from typing import Dict
import numpy as np
from market_state.regime_detector import MarketRegime


class StateMachine:
    def __init__(self):
        self.regimes = list(MarketRegime)
        self.n = len(self.regimes)
        self._index = {r: i for i, r in enumerate(self.regimes)}
        default_prob = (1.0 - 0.7) / (self.n - 1) if self.n > 1 else 0.0
        self.transition_matrix = np.full((self.n, self.n), default_prob, dtype=float)
        np.fill_diagonal(self.transition_matrix, 0.7)
        self.counts = np.zeros((self.n, self.n), dtype=int)
        self._last_regime = None

    def update(self, regime: MarketRegime):
        if self._last_regime is not None:
            i, j = self._index[self._last_regime], self._index[regime]
            self.counts[i, j] += 1
            row_sum = self.counts[i].sum()
            if row_sum > 0:
                self.transition_matrix[i, :] = self.counts[i, :] / row_sum
        self._last_regime = regime

    def predict_next(self, current: MarketRegime) -> MarketRegime:
        i = self._index[current]
        return self.regimes[int(np.argmax(self.transition_matrix[i]))]

    def transition_probs(self, from_regime: MarketRegime) -> Dict[MarketRegime, float]:
        i = self._index[from_regime]
        return {self.regimes[j]: float(self.transition_matrix[i, j]) for j in range(self.n)}
