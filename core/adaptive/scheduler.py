from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from .bayesian_optimizer import BayesianOptimizer, ParameterSpace
from .parameter_store import ParameterStore
from .walk_forward_validator import WalkForwardValidator


@dataclass
class OptimizationTask:
    task_id: str
    strategy_name: str
    param_space: List[ParameterSpace]
    objective: Callable[[Dict[str, float]], float]
    n_iterations: int
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)


class OptimizationScheduler:
    def __init__(
        self,
        parameter_store: ParameterStore,
        validator: Optional[WalkForwardValidator] = None,
        max_concurrent: int = 1,
    ):
        self.parameter_store = parameter_store
        self.validator = validator
        self.max_concurrent = max_concurrent
        self.tasks: List[OptimizationTask] = []
        self._active_count = 0

    def submit_task(
        self,
        strategy_name: str,
        param_space: List[ParameterSpace],
        objective: Callable[[Dict[str, float]], float],
        n_iterations: int = 20,
    ) -> str:
        import uuid

        task_id = str(uuid.uuid4())
        task = OptimizationTask(
            task_id=task_id,
            strategy_name=strategy_name,
            param_space=param_space,
            objective=objective,
            n_iterations=n_iterations,
        )
        self.tasks.append(task)
        logger.info(f"Submitted optimization task {task_id[:8]} for {strategy_name}")
        return task_id

    def run_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        task = self._find_task(task_id)
        if task is None:
            return None

        if self._active_count >= self.max_concurrent:
            logger.warning(f"Max concurrent tasks reached, deferring {task_id[:8]}")
            return None

        task.status = "running"
        self._active_count += 1

        try:
            optimizer = BayesianOptimizer(
                param_space=task.param_space,
                objective=task.objective,
                random_state=42,
            )
            best_params, best_score = optimizer.optimize(task.n_iterations)

            self.parameter_store.save(
                strategy_name=task.strategy_name,
                params=best_params,
                score=best_score,
                metadata={"task_id": task.task_id},
            )

            task.status = "completed"
            task.result = {
                "best_params": best_params,
                "best_score": best_score,
                "trials": len(optimizer.trials),
            }

            logger.info(
                f"Task {task_id[:8]} completed: score={best_score:.6f}"
            )
            return task.result

        except Exception as e:
            task.status = "failed"
            task.result = {"error": str(e)}
            logger.error(f"Task {task_id[:8]} failed: {e}")
            return None

        finally:
            self._active_count -= 1

    def run_all(self) -> List[Dict[str, Any]]:
        results = []
        for task in self.tasks:
            if task.status == "pending":
                result = self.run_task(task.task_id)
                results.append(result)
        return results

    def _find_task(self, task_id: str) -> Optional[OptimizationTask]:
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None

    def get_task_status(self, task_id: str) -> Optional[str]:
        task = self._find_task(task_id)
        return task.status if task else None

    def get_completed_tasks(self) -> List[OptimizationTask]:
        return [t for t in self.tasks if t.status == "completed"]

    def get_pending_tasks(self) -> List[OptimizationTask]:
        return [t for t in self.tasks if t.status == "pending"]
