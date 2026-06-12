from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from .bayesian_optimizer import BayesianOptimizer, ParameterSpace


class RegimeAwareOptimizer:
    def __init__(
        self,
        param_space: List[ParameterSpace],
        objective: Callable[[Dict[str, float], str], float],
        regime_detector: Optional[Callable[[Any], str]] = None,
        n_initial: int = 5,
        random_state: Optional[int] = None,
    ):
        self.param_space = param_space
        self.objective = objective
        self.regime_detector = regime_detector or self._default_regime_detector
        self.optimizers: Dict[str, BayesianOptimizer] = {}
        self.n_initial = n_initial
        self.random_state = random_state

    def _default_regime_detector(self, data: Any) -> str:
        return "neutral"

    def _get_optimizer(self, regime: str) -> BayesianOptimizer:
        if regime not in self.optimizers:
            self.optimizers[regime] = BayesianOptimizer(
                param_space=self.param_space,
                objective=lambda params: self.objective(params, regime),
                n_initial=self.n_initial,
                random_state=self.random_state,
            )
        return self.optimizers[regime]

    def suggest_next(self, current_regime: str) -> Dict[str, float]:
        optimizer = self._get_optimizer(current_regime)
        return optimizer.suggest_next()

    def update(
        self, params: Dict[str, float], score: float, regime: str
    ) -> None:
        optimizer = self._get_optimizer(regime)
        optimizer.update(params, score)

    def optimize(
        self, data: Any, n_iterations: int = 20
    ) -> Dict[str, Any]:
        regime = self.regime_detector(data)
        optimizer = self._get_optimizer(regime)
        best_params, best_score = optimizer.optimize(n_iterations)
        return {
            "regime": regime,
            "best_params": best_params,
            "best_score": best_score,
        }

    def get_regime_params(self, regime: str) -> Optional[Dict[str, float]]:
        if regime in self.optimizers:
            best_params, _ = self.optimizers[regime].best
            return best_params
        return None

    def get_all_regime_params(self) -> Dict[str, Optional[Dict[str, float]]]:
        result = {}
        for regime, optimizer in self.optimizers.items():
            best_params, _ = optimizer.best
            result[regime] = best_params
        return result
