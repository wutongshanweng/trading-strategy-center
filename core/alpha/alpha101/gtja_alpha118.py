"""GTJA Alpha118: (0 - (1 * ((2 * RANK(STD((CLOSE / OPEN), 2))) + RANK(((CLOSE / OPEN) - 1)))))"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha118(AlphaFactor):
    """GTJA Alpha118: (0 - (1 * ((2 * RANK(STD((CLOSE / OPEN), 2))) + RANK(((CLOSE / OPEN) - 1)))))"""

    @property
    def name(self) -> str:
        return "gtja_alpha118"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(0 - (1 * ((2 * RANK(STD((CLOSE / OPEN), 2))) + RANK(((CLOSE / OPEN) - 1)))))"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(0 - (1 * ((2 * RANK(STD((CLOSE / OPEN), 2))) + RANK(((CLOSE / OPEN) - 1)))))"
        return evaluate_gtja(formula, data)
