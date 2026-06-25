"""GTJA Alpha38: (((SUM(HIGH, 20) / 20) < HIGH) ? (-1 * DELTA(HIGH, 2)) : 0)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha38(AlphaFactor):
    """GTJA Alpha38: (((SUM(HIGH, 20) / 20) < HIGH) ? (-1 * DELTA(HIGH, 2)) : 0)"""

    @property
    def name(self) -> str:
        return "gtja_alpha38"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(((SUM(HIGH, 20) / 20) < HIGH) ? (-1 * DELTA(HIGH, 2)) : 0)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(((SUM(HIGH, 20) / 20) < HIGH) ? (-1 * DELTA(HIGH, 2)) : 0)"
        return evaluate_gtja(formula, data)
