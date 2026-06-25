"""GTJA Alpha32: (-1 * SUM(RANK(CORR(RANK(HIGH), RANK(VOLUME), 3)), 3))"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha32(AlphaFactor):
    """GTJA Alpha32: (-1 * SUM(RANK(CORR(RANK(HIGH), RANK(VOLUME), 3)), 3))"""

    @property
    def name(self) -> str:
        return "gtja_alpha32"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(-1 * SUM(RANK(CORR(RANK(HIGH), RANK(VOLUME), 3)), 3))"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(-1 * SUM(RANK(CORR(RANK(HIGH), RANK(VOLUME), 3)), 3))"
        return evaluate_gtja(formula, data)
