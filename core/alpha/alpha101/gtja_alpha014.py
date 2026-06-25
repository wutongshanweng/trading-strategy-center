"""GTJA Alpha14: CLOSE-DELAY(CLOSE,5)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha14(AlphaFactor):
    """GTJA Alpha14: CLOSE-DELAY(CLOSE,5)"""

    @property
    def name(self) -> str:
        return "gtja_alpha14"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "CLOSE-DELAY(CLOSE,5)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "CLOSE-DELAY(CLOSE,5)"
        return evaluate_gtja(formula, data)
