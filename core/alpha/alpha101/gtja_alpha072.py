"""GTJA Alpha72: MIN(RANK(DECAYLINEAR(((((HIGH + LOW) / 2) + HIGH) - (VWAP + HIGH)), 20)), RANK(D"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha72(AlphaFactor):
    """GTJA Alpha72: MIN(RANK(DECAYLINEAR(((((HIGH + LOW) / 2) + HIGH) - (VWAP + HIGH)), 20)), RANK(D"""

    @property
    def name(self) -> str:
        return "gtja_alpha72"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "MIN(RANK(DECAYLINEAR(((((HIGH + LOW) / 2) + HIGH) - (VWAP + HIGH)), 20)), RANK(D"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "MIN(RANK(DECAYLINEAR(((((HIGH + LOW) / 2) + HIGH) - (VWAP + HIGH)), 20)), RANK(DECAYLINEAR(CORR(((HIGH + LOW) / 2), MEAN(VOLUME,40), 3), 6)))"
        return evaluate_gtja(formula, data)
