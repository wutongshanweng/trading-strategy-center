"""GTJA Alpha36: RANK(SUM(CORR(RANK(VOLUME), RANK(VWAP)), 6), 2)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha36(AlphaFactor):
    """GTJA Alpha36: RANK(SUM(CORR(RANK(VOLUME), RANK(VWAP)), 6), 2)"""

    @property
    def name(self) -> str:
        return "gtja_alpha36"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "RANK(SUM(CORR(RANK(VOLUME), RANK(VWAP)), 6), 2)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "RANK(SUM(CORR(RANK(VOLUME), RANK(VWAP)), 6), 2)"
        return evaluate_gtja(formula, data)
