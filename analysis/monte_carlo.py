from typing import Dict
import numpy as np


class MonteCarloStrategyEvaluator:
    def __init__(self, random_state: int = None):
        self.rng = np.random.default_rng(random_state)

    def evaluate(self, strategy_returns: np.ndarray, n_simulations: int = 1000) -> Dict:
        arr = np.asarray(strategy_returns, dtype=float)
        arr = arr[~np.isnan(arr)]
        if len(arr) < 5:
            return {}
        actual_sharpe = float(np.mean(arr) / (np.std(arr, ddof=1) or 1e-10))
        sim = np.array([np.mean(self.rng.permutation(arr)) / (np.std(self.rng.permutation(arr), ddof=1) + 1e-10)
                        for _ in range(n_simulations)])
        lower, upper = np.percentile(sim, [2.5, 97.5])
        return {"actual_sharpe": actual_sharpe, "simulated_mean": float(np.mean(sim)),
                "ci_95": (float(lower), float(upper)), "p_value": float(np.mean(sim >= actual_sharpe))}

    def confidence_interval(self, metric_values: np.ndarray, alpha: float = 0.05):
        arr = np.asarray(metric_values, dtype=float)
        arr = arr[~np.isnan(arr)]
        if len(arr) < 2:
            return (np.nan, np.nan)
        return (float(np.percentile(arr, (alpha / 2) * 100)), float(np.percentile(arr, (1 - alpha / 2) * 100)))
