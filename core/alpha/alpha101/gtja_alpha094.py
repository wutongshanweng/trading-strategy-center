"""GTJA Alpha94: (-1 * RANK(COVIANCE(RANK(CLOSE), RANK(VOLUME), 5)))"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha94(AlphaFactor):
    """GTJA Alpha94: (-1 * RANK(COVIANCE(RANK(CLOSE), RANK(VOLUME), 5)))"""

    @property
    def name(self) -> str:
        return "gtja_alpha94"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(-1 * RANK(COVIANCE(RANK(CLOSE), RANK(VOLUME), 5)))"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(-1 * RANK(COVIANCE(RANK(CLOSE), RANK(VOLUME), 5)))"
        return evaluate_gtja(formula, data)
