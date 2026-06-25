"""GTJA Alpha26: ((((SUM(CLOSE, 7) / 7) - CLOSE)) + ((CORR(VWAP, DELAY(CLOSE, 5), 230))))"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha26(AlphaFactor):
    """GTJA Alpha26: ((((SUM(CLOSE, 7) / 7) - CLOSE)) + ((CORR(VWAP, DELAY(CLOSE, 5), 230))))"""

    @property
    def name(self) -> str:
        return "gtja_alpha26"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "((((SUM(CLOSE, 7) / 7) - CLOSE)) + ((CORR(VWAP, DELAY(CLOSE, 5), 230))))"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "((((SUM(CLOSE, 7) / 7) - CLOSE)) + ((CORR(VWAP, DELAY(CLOSE, 5), 230))))"
        return evaluate_gtja(formula, data)
