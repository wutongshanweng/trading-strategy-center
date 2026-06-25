"""GTJA Alpha114: (RANK((VWAP - CLOSE)) / RANK((VWAP + CLOSE)))"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha114(AlphaFactor):
    """GTJA Alpha114: (RANK((VWAP - CLOSE)) / RANK((VWAP + CLOSE)))"""

    @property
    def name(self) -> str:
        return "gtja_alpha114"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(RANK((VWAP - CLOSE)) / RANK((VWAP + CLOSE)))"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(RANK((VWAP - CLOSE)) / RANK((VWAP + CLOSE)))"
        return evaluate_gtja(formula, data)
