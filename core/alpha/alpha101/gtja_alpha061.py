"""GTJA Alpha61: (CLOSE-MEAN(CLOSE,6))/MEAN(CLOSE,6)*100"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha61(AlphaFactor):
    """GTJA Alpha61: (CLOSE-MEAN(CLOSE,6))/MEAN(CLOSE,6)*100"""

    @property
    def name(self) -> str:
        return "gtja_alpha61"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(CLOSE-MEAN(CLOSE,6))/MEAN(CLOSE,6)*100"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(CLOSE-MEAN(CLOSE,6))/MEAN(CLOSE,6)*100"
        return evaluate_gtja(formula, data)
