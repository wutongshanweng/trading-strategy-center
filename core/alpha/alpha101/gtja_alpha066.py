"""GTJA Alpha66: (CLOSE-MEAN(CLOSE,24))/MEAN(CLOSE,24)*100"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha66(AlphaFactor):
    """GTJA Alpha66: (CLOSE-MEAN(CLOSE,24))/MEAN(CLOSE,24)*100"""

    @property
    def name(self) -> str:
        return "gtja_alpha66"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(CLOSE-MEAN(CLOSE,24))/MEAN(CLOSE,24)*100"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(CLOSE-MEAN(CLOSE,24))/MEAN(CLOSE,24)*100"
        return evaluate_gtja(formula, data)
