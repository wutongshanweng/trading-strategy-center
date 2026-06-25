"""GTJA Alpha15: OPEN/DELAY(CLOSE,1)-1"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha15(AlphaFactor):
    """GTJA Alpha15: OPEN/DELAY(CLOSE,1)-1"""

    @property
    def name(self) -> str:
        return "gtja_alpha15"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "OPEN/DELAY(CLOSE,1)-1"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "OPEN/DELAY(CLOSE,1)-1"
        return evaluate_gtja(formula, data)
