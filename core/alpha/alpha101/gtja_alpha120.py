"""GTJA Alpha120: (CLOSE+HIGH+LOW)/3"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha120(AlphaFactor):
    """GTJA Alpha120: (CLOSE+HIGH+LOW)/3"""

    @property
    def name(self) -> str:
        return "gtja_alpha120"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(CLOSE+HIGH+LOW)/3"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(CLOSE+HIGH+LOW)/3"
        return evaluate_gtja(formula, data)
