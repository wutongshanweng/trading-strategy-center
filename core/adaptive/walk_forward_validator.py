from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger


@dataclass
class WindowResult:
    window_id: int
    train_start: int
    train_end: int
    test_start: int
    test_end: int
    in_sample_score: float
    out_sample_score: float
    params: Dict[str, float]
    oos_degradation: float = 0.0

    def __post_init__(self):
        if self.in_sample_score != 0:
            self.oos_degradation = (
                self.out_sample_score - self.in_sample_score
            ) / abs(self.in_sample_score)


@dataclass
class ValidationReport:
    n_windows: int
    mean_oos_score: float
    std_oos_score: float
    mean_degradation: float
    overfit_ratio: float
    windows: List[WindowResult]
    is_robust: bool = True

    def __post_init__(self):
        if self.mean_degradation < -0.3:
            self.is_robust = False


class WalkForwardValidator:
    def __init__(
        self,
        train_ratio: float = 0.7,
        n_splits: int = 5,
        expanding: bool = True,
        min_train_size: int = 100,
    ):
        self.train_ratio = train_ratio
        self.n_splits = n_splits
        self.expanding = expanding
        self.min_train_size = min_train_size

    def split(
        self, n_observations: int
    ) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        splits = []
        test_size = int(n_observations * (1 - self.train_ratio) / self.n_splits)
        train_size = int(n_observations * self.train_ratio)

        for i in range(self.n_splits):
            if self.expanding:
                train_start = 0
            else:
                train_start = i * test_size

            train_end = train_start + train_size
            test_start = train_end
            test_end = test_start + test_size

            if test_end > n_observations:
                break

            if train_end - train_start < self.min_train_size:
                continue

            splits.append(((train_start, train_end), (test_start, test_end)))

        return splits

    def validate(
        self,
        data: Any,
        objective: Callable[[Dict[str, float], Any], float],
        optimizer_class: Any,
        param_space: List[Any],
        n_optimization_iter: int = 10,
    ) -> ValidationReport:
        n_obs = len(data)
        splits = self.split(n_obs)
        window_results: List[WindowResult] = []

        for window_id, ((train_start, train_end), (test_start, test_end)) in enumerate(
            splits
        ):
            train_data = data.iloc[train_start:train_end]
            test_data = data.iloc[test_start:test_end]

            optimizer = optimizer_class(
                param_space=param_space,
                objective=lambda params: objective(params, train_data),
                random_state=42,
            )
            best_params, in_sample_score = optimizer.optimize(n_optimization_iter)

            out_sample_score = objective(best_params, test_data)

            window_result = WindowResult(
                window_id=window_id,
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
                in_sample_score=in_sample_score,
                out_sample_score=out_sample_score,
                params=best_params,
            )
            window_results.append(window_result)

            logger.info(
                f"Window {window_id}: IS={in_sample_score:.4f}, "
                f"OOS={out_sample_score:.4f}, "
                f"degradation={window_result.oos_degradation:.2%}"
            )

        oos_scores = [w.out_sample_score for w in window_results]
        degradations = [w.oos_degradation for w in window_results]

        report = ValidationReport(
            n_windows=len(window_results),
            mean_oos_score=float(np.mean(oos_scores)),
            std_oos_score=float(np.std(oos_scores)),
            mean_degradation=float(np.mean(degradations)),
            overfit_ratio=float(
                np.mean([1 for d in degradations if d < -0.1])
                / max(len(degradations), 1)
            ),
            windows=window_results,
        )

        return report

    def check_robustness(self, report: ValidationReport) -> bool:
        return (
            report.is_robust
            and report.mean_degradation > -0.2
            and report.overfit_ratio < 0.3
        )
    
    def detect_overfitting(self, report: ValidationReport) -> bool:
        return report.mean_degradation < -0.3 or report.overfit_ratio > 0.4
