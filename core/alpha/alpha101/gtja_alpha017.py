"""GTJA Alpha17: RANK((VWAP - MAX(VWAP, 15)))^DELTA(CLOSE, 5)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha17(AlphaFactor):
    """GTJA Alpha17: RANK((VWAP - MAX(VWAP, 15)))^DELTA(CLOSE, 5)"""

    @property
    def name(self) -> str:
        return "gtja_alpha17"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "RANK((VWAP - MAX(VWAP, 15)))^DELTA(CLOSE, 5)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "RANK((VWAP - MAX(VWAP, 15)))^DELTA(CLOSE, 5)"
        return evaluate_gtja(formula, data)
