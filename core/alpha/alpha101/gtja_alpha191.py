"""GTJA Alpha191: ((CORR(MEAN(VOLUME,20), LOW, 5) + ((HIGH + LOW) / 2)) - CLOSE)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha191(AlphaFactor):
    """GTJA Alpha191: ((CORR(MEAN(VOLUME,20), LOW, 5) + ((HIGH + LOW) / 2)) - CLOSE)"""

    @property
    def name(self) -> str:
        return "gtja_alpha191"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "((CORR(MEAN(VOLUME,20), LOW, 5) + ((HIGH + LOW) / 2)) - CLOSE)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "((CORR(MEAN(VOLUME,20), LOW, 5) + ((HIGH + LOW) / 2)) - CLOSE)"
        return evaluate_gtja(formula, data)
