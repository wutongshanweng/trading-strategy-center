"""GTJA Alpha20: (CLOSE-DELAY(CLOSE,6))/DELAY(CLOSE,6)*100"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha20(AlphaFactor):
    """GTJA Alpha20: (CLOSE-DELAY(CLOSE,6))/DELAY(CLOSE,6)*100"""

    @property
    def name(self) -> str:
        return "gtja_alpha20"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(CLOSE-DELAY(CLOSE,6))/DELAY(CLOSE,6)*100"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(CLOSE-DELAY(CLOSE,6))/DELAY(CLOSE,6)*100"
        return evaluate_gtja(formula, data)
