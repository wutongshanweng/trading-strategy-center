"""GTJA Alpha41: (RANK(MAX(DELTA((VWAP), 3), 5))* -1)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha41(AlphaFactor):
    """GTJA Alpha41: (RANK(MAX(DELTA((VWAP), 3), 5))* -1)"""

    @property
    def name(self) -> str:
        return "gtja_alpha41"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(RANK(MAX(DELTA((VWAP), 3), 5))* -1)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(RANK(MAX(DELTA((VWAP), 3), 5))* -1)"
        return evaluate_gtja(formula, data)
