"""GTJA Alpha57: (-1 * CORR(HIGH, RANK(VOLUME), 5))"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha57(AlphaFactor):
    """GTJA Alpha57: (-1 * CORR(HIGH, RANK(VOLUME), 5))"""

    @property
    def name(self) -> str:
        return "gtja_alpha57"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(-1 * CORR(HIGH, RANK(VOLUME), 5))"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(-1 * CORR(HIGH, RANK(VOLUME), 5))"
        return evaluate_gtja(formula, data)
