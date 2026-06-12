from typing import Dict, List


class RankingSystem:
    def __init__(self, k_factor: int = 32):
        self.k_factor = k_factor
        self._ratings: Dict[str, float] = {}

    def _expected_score(self, rating_a: float, rating_b: float) -> float:
        return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))

    def update_rankings(self, winner: str, loser: str):
        if winner not in self._ratings:
            self._ratings[winner] = 1200.0
        if loser not in self._ratings:
            self._ratings[loser] = 1200.0
        e_winner = self._expected_score(self._ratings[winner], self._ratings[loser])
        e_loser = self._expected_score(self._ratings[loser], self._ratings[winner])
        self._ratings[winner] += self.k_factor * (1.0 - e_winner)
        self._ratings[loser] += self.k_factor * (0.0 - e_loser)

    def get_ranking(self, name: str) -> float:
        return self._ratings.get(name, 1200.0)

    def get_all_rankings(self) -> Dict[str, float]:
        return dict(sorted(self._ratings.items(), key=lambda x: x[1], reverse=True))
