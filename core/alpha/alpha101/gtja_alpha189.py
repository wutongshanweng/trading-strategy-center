"""GTJA Alpha189: MEAN(ABS(CLOSE-MEAN(CLOSE,6)),6)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha189(AlphaFactor):
    """GTJA Alpha189: MEAN(ABS(CLOSE-MEAN(CLOSE,6)),6)"""

    @property
    def name(self) -> str:
        return "gtja_alpha189"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "MEAN(ABS(CLOSE-MEAN(CLOSE,6)),6)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "MEAN(ABS(CLOSE-MEAN(CLOSE,6)),6)"
        return evaluate_gtja(formula, data)
