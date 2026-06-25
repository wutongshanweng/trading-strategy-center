"""GTJA Alpha52: COUNT(CLOSE>DELAY(CLOSE,1),12)/12*100"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha52(AlphaFactor):
    """GTJA Alpha52: COUNT(CLOSE>DELAY(CLOSE,1),12)/12*100"""

    @property
    def name(self) -> str:
        return "gtja_alpha52"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "COUNT(CLOSE>DELAY(CLOSE,1),12)/12*100"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "COUNT(CLOSE>DELAY(CLOSE,1),12)/12*100"
        return evaluate_gtja(formula, data)
