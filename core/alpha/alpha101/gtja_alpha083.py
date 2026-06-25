"""GTJA Alpha83: (CLOSE-DELAY(CLOSE,20))/DELAY(CLOSE,20)*100"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha83(AlphaFactor):
    """GTJA Alpha83: (CLOSE-DELAY(CLOSE,20))/DELAY(CLOSE,20)*100"""

    @property
    def name(self) -> str:
        return "gtja_alpha83"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(CLOSE-DELAY(CLOSE,20))/DELAY(CLOSE,20)*100"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(CLOSE-DELAY(CLOSE,20))/DELAY(CLOSE,20)*100"
        return evaluate_gtja(formula, data)
