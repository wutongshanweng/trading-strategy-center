"""GTJA Alpha7: ((RANK(MAX((VWAP - CLOSE), 3)) + RANK(MIN((VWAP - CLOSE), 3))) * RANK(DELTA(VOLU"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha7(AlphaFactor):
    """GTJA Alpha7: ((RANK(MAX((VWAP - CLOSE), 3)) + RANK(MIN((VWAP - CLOSE), 3))) * RANK(DELTA(VOLU"""

    @property
    def name(self) -> str:
        return "gtja_alpha7"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "((RANK(MAX((VWAP - CLOSE), 3)) + RANK(MIN((VWAP - CLOSE), 3))) * RANK(DELTA(VOLU"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "((RANK(MAX((VWAP - CLOSE), 3)) + RANK(MIN((VWAP - CLOSE), 3))) * RANK(DELTA(VOLUME, 3)))"
        return evaluate_gtja(formula, data)
