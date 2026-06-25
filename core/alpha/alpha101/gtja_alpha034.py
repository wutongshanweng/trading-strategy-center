"""GTJA Alpha34: MEAN(CLOSE,12)/CLOSE"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha34(AlphaFactor):
    """GTJA Alpha34: MEAN(CLOSE,12)/CLOSE"""

    @property
    def name(self) -> str:
        return "gtja_alpha34"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "MEAN(CLOSE,12)/CLOSE"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "MEAN(CLOSE,12)/CLOSE"
        return evaluate_gtja(formula, data)
