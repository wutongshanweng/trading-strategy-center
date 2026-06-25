"""GTJA Alpha90: STD(AMOUNT,20)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha90(AlphaFactor):
    """GTJA Alpha90: STD(AMOUNT,20)"""

    @property
    def name(self) -> str:
        return "gtja_alpha90"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "STD(AMOUNT,20)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "STD(AMOUNT,20)"
        return evaluate_gtja(formula, data)
