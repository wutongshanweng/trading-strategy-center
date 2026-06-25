"""GTJA Alpha185: RANK((-1 * ((1 - (OPEN / CLOSE))^2)))"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha185(AlphaFactor):
    """GTJA Alpha185: RANK((-1 * ((1 - (OPEN / CLOSE))^2)))"""

    @property
    def name(self) -> str:
        return "gtja_alpha185"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "RANK((-1 * ((1 - (OPEN / CLOSE))^2)))"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "RANK((-1 * ((1 - (OPEN / CLOSE))^2)))"
        return evaluate_gtja(formula, data)
