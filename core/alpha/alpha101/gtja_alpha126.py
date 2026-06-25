"""GTJA Alpha126: MEAN(AMOUNT,20)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha126(AlphaFactor):
    """GTJA Alpha126: MEAN(AMOUNT,20)"""

    @property
    def name(self) -> str:
        return "gtja_alpha126"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "MEAN(AMOUNT,20)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "MEAN(AMOUNT,20)"
        return evaluate_gtja(formula, data)
