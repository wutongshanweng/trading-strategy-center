"""Genetic Programming Factor Mining Engine.

Uses evolutionary algorithms to automatically discover new alpha factors
by combining basic operations on OHLCV data.
"""

import random
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd
from loguru import logger


class OperatorLibrary:
    """Library of operators for genetic programming factor construction."""

    @staticmethod
    def arithmetic_ops() -> Dict[str, Callable]:
        """Binary arithmetic operators."""
        def _div(a: pd.Series, b: pd.Series) -> pd.Series:
            return np.where(b != 0, a / b, 0.0)

        return {
            "add": lambda a, b: a + b,
            "sub": lambda a, b: a - b,
            "mul": lambda a, b: a * b,
            "div": _div,
        }

    @staticmethod
    def comparison_ops() -> Dict[str, Callable]:
        """Binary comparison operators."""
        return {
            "max": lambda a, b: np.maximum(a, b),
            "min": lambda a, b: np.minimum(a, b),
            "gt": lambda a, b: (a > b).astype(float),
            "lt": lambda a, b: (a < b).astype(float),
        }

    @staticmethod
    def time_series_ops() -> Dict[str, Callable]:
        """Unary time-series operators with a window parameter."""
        return {
            "ts_mean": lambda x, w: x.rolling(int(w), min_periods=1).mean(),
            "ts_std": lambda x, w: x.rolling(int(w), min_periods=1).std(),
            "ts_max": lambda x, w: x.rolling(int(w), min_periods=1).max(),
            "ts_min": lambda x, w: x.rolling(int(w), min_periods=1).min(),
            "ts_rank": lambda x, w: x.rolling(int(w), min_periods=1).rank(),
            "delay": lambda x, w: x.shift(int(w)),
            "delta": lambda x, w: x - x.shift(int(w)),
        }

    @staticmethod
    def unary_ops() -> Dict[str, Callable]:
        """Unary pointwise operators."""
        return {
            "abs": lambda x: np.abs(x),
            "neg": lambda x: -x,
            "sign": lambda x: np.sign(x),
            "log": lambda x: np.log(np.abs(x) + 1e-8),
            "zscore": lambda x: (x - x.rolling(20, min_periods=1).mean())
            / (x.rolling(20, min_periods=1).std() + 1e-8),
            "rank": lambda x: x.rank(pct=True),
        }

    @classmethod
    def get_all_ops(cls) -> Dict[str, Callable]:
        """Return all operators merged into one dict."""
        ops: Dict[str, Callable] = {}
        for method in (
            cls.arithmetic_ops,
            cls.comparison_ops,
            cls.time_series_ops,
            cls.unary_ops,
        ):
            ops.update(method())
        return ops


class FactorExpression:
    """A callable factor expression built by genetic programming."""

    def __init__(
        self,
        expression: Callable[[pd.DataFrame], pd.Series],
        name: Optional[str] = None,
    ):
        self.expression = expression
        self.name = name or f"gp_factor_{id(self)}"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """Compute factor values from OHLCV data."""
        return self.expression(data)

    def __repr__(self) -> str:
        return f"FactorExpression({self.name})"


# ---- helpers -----------------------------------------------------------

COLUMNS = ["open", "high", "low", "close", "volume"]


def _random_leaf() -> Callable:
    """Return a lambda that fetches a random column."""
    col = random.choice(COLUMNS)
    return lambda data: data[col].astype(float)





def _build_random_tree(max_depth: int = 2) -> Callable:
    """Build a random expression tree of limited depth."""
    ops = OperatorLibrary.get_all_ops()
    binary_names = list(
        list(OperatorLibrary.arithmetic_ops().keys())
        + list(OperatorLibrary.comparison_ops().keys())
    )
    ts_names = list(OperatorLibrary.time_series_ops().keys())
    unary_names = list(OperatorLibrary.unary_ops().keys())

    def _tree(depth: int) -> Callable:
        if depth <= 0 or random.random() < 0.3:
            return _random_leaf()

        kind = random.choices(
            ["binary", "ts", "unary"], weights=[0.4, 0.4, 0.2], k=1
        )[0]

        if kind == "binary":
            op_name = random.choice(binary_names)
            op = ops[op_name]
            left = _tree(depth - 1)
            right = _tree(depth - 1)
            return lambda data, _op=op, _l=left, _r=right: _op(_l(data), _r(data))

        if kind == "ts":
            op_name = random.choice(ts_names)
            op = ops[op_name]
            child = _tree(depth - 1)
            w = random.randint(5, 30)
            return lambda data, _op=op, _c=child, _w=w: _op(_c(data), _w)

        # unary
        op_name = random.choice(unary_names)
        op = ops[op_name]
        child = _tree(depth - 1)
        return lambda data, _op=op, _c=child: _op(_c(data))

    return _tree(max_depth)


# ---- fitness -----------------------------------------------------------


class FitnessFunction:
    """Evaluate factor quality using IC, IR, turnover, and decay."""

    def __init__(
        self,
        ic_weight: float = 0.4,
        ir_weight: float = 0.3,
        turnover_weight: float = 0.2,
        decay_weight: float = 0.1,
    ):
        self.ic_weight = ic_weight
        self.ir_weight = ir_weight
        self.turnover_weight = turnover_weight
        self.decay_weight = decay_weight

    def evaluate(
        self,
        factor: FactorExpression,
        data: pd.DataFrame,
        returns: Optional[pd.Series] = None,
    ) -> float:
        """Return a fitness score (higher is better)."""
        try:
            factor_values = factor.compute(data)
            if returns is None:
                returns = data["close"].pct_change()

            fv = factor_values.dropna()
            rv = returns.loc[fv.index].dropna()
            common = fv.index.intersection(rv.index)
            if len(common) < 30:
                return 0.0

            fv = fv.loc[common]
            rv = rv.loc[common]

            ic = float(fv.corr(rv))
            if np.isnan(ic):
                return 0.0

            # rolling IR
            rolling_ic = fv.rolling(20, min_periods=10).corr(rv)
            ir_std = float(rolling_ic.std())
            ir = ic / ir_std if ir_std > 0 else 0.0

            turnover = float(fv.diff().abs().mean())

            decay = self._calc_decay(fv, rv)

            fitness = (
                self.ic_weight * abs(ic)
                + self.ir_weight * abs(ir)
                - self.turnover_weight * turnover
                - self.decay_weight * decay
            )
            return max(fitness, 0.0)
        except Exception as exc:
            logger.debug(f"Fitness eval failed: {exc}")
            return 0.0

    @staticmethod
    def _calc_decay(fv: pd.Series, rv: pd.Series) -> float:
        try:
            lags = range(1, 6)
            corrs = [fv.shift(lag).corr(rv) for lag in lags]
            corrs = [c for c in corrs if not np.isnan(c)]
            if len(corrs) > 1:
                return abs(float(np.mean(np.diff(corrs))))
            return 0.0
        except Exception:
            return 0.0


# ---- genetic programming engine ----------------------------------------


class GeneticProgramming:
    """Evolutionary engine for automatic factor discovery."""

    def __init__(
        self,
        population_size: int = 50,
        generations: int = 20,
        crossover_rate: float = 0.7,
        mutation_rate: float = 0.2,
        tournament_size: int = 5,
        max_depth: int = 3,
    ):
        self.population_size = population_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.max_depth = max_depth

    def evolve(
        self,
        data: pd.DataFrame,
        fitness_fn: Optional[FitnessFunction] = None,
        returns: Optional[pd.Series] = None,
        top_k: int = 10,
    ) -> List[FactorExpression]:
        """Run the evolutionary loop and return the best factor expressions."""
        if fitness_fn is None:
            fitness_fn = FitnessFunction()
        if returns is None:
            returns = data["close"].pct_change()

        population = self._init_population()
        best_history: list = []

        for gen in range(self.generations):
            scores = [
                fitness_fn.evaluate(ind, data, returns) for ind in population
            ]
            for s, ind in zip(scores, population):
                best_history.append((s, ind))

            selected = self._tournament_select(population, scores)
            offspring = self._crossover(selected)
            population = self._mutate(offspring)

            best_score = max(scores) if scores else 0.0
            logger.debug(f"Gen {gen}: best_score={best_score:.6f}")

        # final evaluation
        final_scores = [fitness_fn.evaluate(ind, data, returns) for ind in population]
        ranked = sorted(
            zip(final_scores, population), key=lambda x: x[0], reverse=True
        )
        return [ind for _score, ind in ranked[:top_k]]

    # ---- internal -------------------------------------------------------

    def _init_population(self) -> List[FactorExpression]:
        return [
            FactorExpression(_build_random_tree(self.max_depth))
            for _ in range(self.population_size)
        ]

    def _tournament_select(
        self,
        population: List[FactorExpression],
        scores: List[float],
    ) -> List[FactorExpression]:
        selected: List[FactorExpression] = []
        for _ in range(len(population)):
            indices = random.sample(
                range(len(population)),
                min(self.tournament_size, len(population)),
            )
            best_idx = max(indices, key=lambda i: scores[i])
            selected.append(population[best_idx])
        return selected

    def _crossover(
        self, population: List[FactorExpression]
    ) -> List[FactorExpression]:
        offspring: List[FactorExpression] = []
        for i in range(0, len(population) - 1, 2):
            p1, p2 = population[i], population[i + 1]
            if random.random() < self.crossover_rate:
                offspring.append(
                    FactorExpression(p2.expression, f"crossover_{i}")
                )
                offspring.append(
                    FactorExpression(p1.expression, f"crossover_{i+1}")
                )
            else:
                offspring.append(p1)
                offspring.append(p2)
        if len(population) % 2 == 1:
            offspring.append(population[-1])
        return offspring

    def _mutate(
        self, population: List[FactorExpression]
    ) -> List[FactorExpression]:
        mutated: List[FactorExpression] = []
        for ind in population:
            if random.random() < self.mutation_rate:
                mutated.append(
                    FactorExpression(
                        _build_random_tree(self.max_depth),
                        f"mutated_{ind.name}",
                    )
                )
            else:
                mutated.append(ind)
        return mutated


# ---- factor synthesizer ------------------------------------------------


class FactorSynthesizer:
    """Combine multiple FactorExpressions into a single composite factor."""

    def __init__(self, factors: Optional[List[FactorExpression]] = None):
        self.factors: List[FactorExpression] = factors or []

    def add_factor(self, factor: FactorExpression) -> None:
        self.factors.append(factor)

    def combine(
        self, data: pd.DataFrame, method: str = "mean"
    ) -> pd.Series:
        """Combine all stored factors into a single signal."""
        if not self.factors:
            return pd.Series(0.0, index=data.index)

        values = []
        for f in self.factors:
            try:
                v = f.compute(data)
                values.append(v)
            except Exception:
                continue

        if not values:
            return pd.Series(0.0, index=data.index)

        combined = pd.concat(values, axis=1)
        if method == "mean":
            return combined.mean(axis=1)
        if method == "median":
            return combined.median(axis=1)
        if method == "sum":
            return combined.sum(axis=1)
        return combined.mean(axis=1)


# ---------------------------------------------------------------------------
# Phase 2 扩展: 函数式算子集 (见 operator_set.py)
# ---------------------------------------------------------------------------
from .operator_set import (  # noqa: E402
    get_operator,
    get_operators,
    apply_operator,
    TS_OPERATORS,
    MATH_OPERATORS,
    BINARY_OPERATORS,
)

from .genetic_programming import (  # noqa: E402
    GeneticFactorMiner,
    MinedFactor,
    GeneticConfig,
)
