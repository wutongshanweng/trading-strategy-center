"""GTJA Alpha8: RANK(DELTA(((((HIGH + LOW) / 2) * 0.2) + (VWAP * 0.8)), 4) * -1)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha8(AlphaFactor):
    """GTJA Alpha8: RANK(DELTA(((((HIGH + LOW) / 2) * 0.2) + (VWAP * 0.8)), 4) * -1)"""

    @property
    def name(self) -> str:
        return "gtja_alpha8"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "RANK(DELTA(((((HIGH + LOW) / 2) * 0.2) + (VWAP * 0.8)), 4) * -1)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "RANK(DELTA(((((HIGH + LOW) / 2) * 0.2) + (VWAP * 0.8)), 4) * -1)"
        return evaluate_gtja(formula, data)
