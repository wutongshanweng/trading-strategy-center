"""GTJA Alpha100: CLOSE-DELAY(CLOSE,20)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha100(AlphaFactor):
    """GTJA Alpha100: CLOSE-DELAY(CLOSE,20)"""

    @property
    def name(self) -> str:
        return "gtja_alpha100"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "CLOSE-DELAY(CLOSE,20)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "CLOSE-DELAY(CLOSE,20)"
        return evaluate_gtja(formula, data)
