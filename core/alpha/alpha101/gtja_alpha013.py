"""GTJA Alpha13: (((HIGH * LOW)^0.5) - VWAP)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha13(AlphaFactor):
    """GTJA Alpha13: (((HIGH * LOW)^0.5) - VWAP)"""

    @property
    def name(self) -> str:
        return "gtja_alpha13"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(((HIGH * LOW)^0.5) - VWAP)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(((HIGH * LOW)^0.5) - VWAP)"
        return evaluate_gtja(formula, data)
