"""
超参自动搜索 — Optuna 贝叶斯 / 随机 / 网格。

param_space 格式:
    {"lr": (0.01, 0.3, "float"), "depth": (3, 10, "int"), "k": ["a", "b"]}

用法:
    best_params, best_score = HyperoptSearcher().search(
        train_fn, param_space, n_trials=50, method="optuna")
"""

from __future__ import annotations

from typing import Callable, Dict, Tuple

import numpy as np
from loguru import logger


class HyperoptSearcher:
    """超参自动搜索 (optuna / random / grid)。"""

    def search(
        self,
        train_fn: Callable[[Dict], float],
        param_space: Dict[str, Tuple],
        n_trials: int = 50,
        method: str = "optuna",
        direction: str = "maximize",
        seed: int = 42,
    ) -> Tuple[Dict, float]:
        """执行超参搜索, 返回 (best_params, best_score)。"""
        if method == "optuna":
            return self._optuna_search(train_fn, param_space, n_trials, direction, seed)
        elif method == "random":
            return self._random_search(train_fn, param_space, n_trials, direction, seed)
        elif method == "grid":
            return self._grid_search(train_fn, param_space, direction)
        raise ValueError(f"Unknown method: {method}")

    def _sample_random(self, spec):
        if isinstance(spec, list):
            return np.random.choice(spec)
        if isinstance(spec, tuple) and len(spec) == 3:
            low, high, dtype = spec
            if dtype == "float":
                return float(np.random.uniform(low, high))
            if dtype == "int":
                return int(np.random.randint(low, high + 1))
        return spec

    def _random_search(self, train_fn, param_space, n_trials, direction, seed):
        """随机搜索 (无依赖, 兜底)。"""
        np.random.seed(seed)
        best_params, best_score = None, (-np.inf if direction == "maximize" else np.inf)
        for trial in range(n_trials):
            params = {n: self._sample_random(s) for n, s in param_space.items()}
            try:
                score = train_fn(params)
                if (direction == "maximize" and score > best_score) or \
                   (direction == "minimize" and score < best_score):
                    best_score, best_params = score, params.copy()
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Trial {trial+1} failed: {e}")
        return best_params, best_score

    def _optuna_search(self, train_fn, param_space, n_trials, direction, seed):
        """Optuna 贝叶斯搜索 (缺库回退随机)。"""
        try:
            import optuna
            optuna.logging.set_verbosity(optuna.logging.WARNING)
        except ImportError:
            logger.warning("optuna not installed, falling back to random search")
            return self._random_search(train_fn, param_space, n_trials, direction, seed)

        def objective(trial):
            params = {}
            for name, spec in param_space.items():
                if isinstance(spec, list):
                    params[name] = trial.suggest_categorical(name, spec)
                elif isinstance(spec, tuple) and len(spec) == 3:
                    low, high, dtype = spec
                    if dtype == "float":
                        params[name] = trial.suggest_float(name, low, high)
                    elif dtype == "int":
                        params[name] = trial.suggest_int(name, low, high)
                else:
                    params[name] = spec
            return train_fn(params)

        study = optuna.create_study(
            direction=direction, sampler=optuna.samplers.TPESampler(seed=seed))
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
        logger.info(f"Optuna best: {study.best_value:.4f}")
        return study.best_params, study.best_value

    def _grid_search(self, train_fn, param_space, direction):
        """网格搜索 (参数少时用)。"""
        from itertools import product
        param_names, param_values = [], []
        for name, spec in param_space.items():
            param_names.append(name)
            if isinstance(spec, list):
                param_values.append(spec)
            elif isinstance(spec, tuple) and len(spec) == 3:
                low, high, dtype = spec
                if dtype == "int":
                    param_values.append(list(range(int(low), int(high) + 1)))
                else:
                    param_values.append([round(low + (high - low) * i / 10, 2)
                                         for i in range(11)])
        best_params, best_score = None, (-np.inf if direction == "maximize" else np.inf)
        for values in product(*param_values):
            params = dict(zip(param_names, values))
            try:
                score = train_fn(params)
                if (direction == "maximize" and score > best_score) or \
                   (direction == "minimize" and score < best_score):
                    best_score, best_params = score, params.copy()
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Grid point {params} failed: {e}")
        return best_params, best_score
