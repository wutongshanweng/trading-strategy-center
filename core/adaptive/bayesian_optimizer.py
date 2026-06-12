from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger


@dataclass
class ParameterSpace:
    name: str
    low: float
    high: float
    log_scale: bool = False


@dataclass
class TrialResult:
    trial_id: str
    params: Dict[str, float]
    score: float
    timestamp: float = field(default_factory=time.time)


class BayesianOptimizer:
    def __init__(
        self,
        param_space: List[ParameterSpace],
        objective: Callable[[Dict[str, float]], float],
        n_initial: int = 5,
        random_state: Optional[int] = None,
    ):
        self.param_space = {p.name: p for p in param_space}
        self.objective = objective
        self.n_initial = n_initial
        self.rng = np.random.RandomState(random_state)
        self.trials: List[TrialResult] = []
        self._best_score: Optional[float] = None
        self._best_params: Optional[Dict[str, float]] = None

    def _normalize(self, value: float, space: ParameterSpace) -> float:
        if space.log_scale:
            log_low = np.log(max(space.low, 1e-10))
            log_high = np.log(max(space.high, 1e-10))
            log_val = np.log(max(value, 1e-10))
            return (log_val - log_low) / (log_high - log_low)
        return (value - space.low) / (space.high - space.low)

    def _denormalize(self, norm: float, space: ParameterSpace) -> float:
        if space.log_scale:
            log_low = np.log(max(space.low, 1e-10))
            log_high = np.log(max(space.high, 1e-10))
            log_val = log_low + norm * (log_high - log_low)
            return float(np.exp(log_val))
        return float(space.low + norm * (space.high - space.low))

    def _random_params(self) -> Dict[str, float]:
        params = {}
        for name, space in self.param_space.items():
            norm = self.rng.uniform(0, 1)
            params[name] = self._denormalize(norm, space)
        return params

    def _sample_latin_hypercube(self, n_samples: int) -> List[Dict[str, float]]:
        n_params = len(self.param_space)
        samples = np.zeros((n_samples, n_params))
        for i in range(n_params):
            perm = self.rng.permutation(n_samples)
            for j in range(n_samples):
                samples[j, i] = (perm[j] + self.rng.uniform()) / n_samples

        param_names = list(self.param_space.keys())
        result = []
        for row in samples:
            params = {}
            for k, name in enumerate(param_names):
                params[name] = self._denormalize(row[k], self.param_space[name])
            result.append(params)
        return result

    def _surrogate_predict(
        self, X: np.ndarray, X_observed: np.ndarray, y_observed: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        if len(X_observed) == 0:
            return np.zeros(len(X)), np.ones(len(X))

        length_scale = 1.0

        dist_obs = np.sqrt(((X_observed[:, None] - X_observed[None, :]) ** 2).sum(axis=2))
        K_obs = np.exp(-0.5 * (dist_obs / length_scale) ** 2)
        noise = 1e-6 * np.eye(len(K_obs))
        try:
            K_obs_inv = np.linalg.inv(K_obs + noise)
        except np.linalg.LinAlgError:
            K_obs_inv = np.linalg.pinv(K_obs + noise)

        dist_star = np.sqrt(((X[:, None] - X_observed[None, :]) ** 2).sum(axis=2))
        K_star = np.exp(-0.5 * (dist_star / length_scale) ** 2)

        mu = K_star @ K_obs_inv @ y_observed
        sigma = np.sqrt(
            np.maximum(
                1.0 - np.diag(K_star @ K_obs_inv @ K_star.T), 0
            )
        )
        return mu, sigma

    def _acquisition_ucb(
        self, mu: np.ndarray, sigma: np.ndarray, beta: float = 2.0
    ) -> np.ndarray:
        return mu + beta * sigma

    def suggest_next(self) -> Dict[str, float]:
        if len(self.trials) < self.n_initial:
            return self._random_params()

        param_names = list(self.param_space.keys())
        n_dim = len(param_names)

        X_observed = np.array(
            [
                [self._normalize(t.params[n], self.param_space[n]) for n in param_names]
                for t in self.trials
            ]
        )
        y_observed = np.array([t.score for t in self.trials])

        n_candidates = 1000
        X_candidates = self.rng.uniform(0, 1, (n_candidates, n_dim))

        mu, sigma = self._surrogate_predict(X_candidates, X_observed, y_observed)
        acq = self._acquisition_ucb(mu, sigma)
        best_idx = np.argmax(acq)

        best_candidate = X_candidates[best_idx]
        return {
            name: self._denormalize(best_candidate[i], self.param_space[name])
            for i, name in enumerate(param_names)
        }

    def update(self, params: Dict[str, float], score: float) -> TrialResult:
        trial = TrialResult(
            trial_id=str(uuid.uuid4()),
            params=params,
            score=score,
        )
        self.trials.append(trial)

        if self._best_score is None or score > self._best_score:
            self._best_score = score
            self._best_params = params.copy()

        logger.info(
            f"Trial {trial.trial_id[:8]}: score={score:.6f} "
            f"(best={self._best_score:.6f})"
        )
        return trial

    def optimize(self, n_iterations: int = 20) -> Tuple[Dict[str, float], float]:
        for i in range(n_iterations):
            params = self.suggest_next()
            score = self.objective(params)
            self.update(params, score)
            logger.debug(f"Optimization iteration {i+1}/{n_iterations}")

        return self._best_params, self._best_score

    @property
    def best(self) -> Tuple[Optional[Dict[str, float]], Optional[float]]:
        return self._best_params, self._best_score

    def get_history(self) -> List[Dict[str, Any]]:
        return [asdict(t) for t in self.trials]
