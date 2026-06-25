"""GTJA Alpha124: (RANK(DECAYLINEAR(CORR(((HIGH + LOW) / 2), MEAN(VOLUME,40), 9), 10)) / RANK(DECA"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha124(AlphaFactor):
    """GTJA Alpha124: (RANK(DECAYLINEAR(CORR(((HIGH + LOW) / 2), MEAN(VOLUME,40), 9), 10)) / RANK(DECA"""

    @property
    def name(self) -> str:
        return "gtja_alpha124"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(RANK(DECAYLINEAR(CORR(((HIGH + LOW) / 2), MEAN(VOLUME,40), 9), 10)) / RANK(DECA"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(RANK(DECAYLINEAR(CORR(((HIGH + LOW) / 2), MEAN(VOLUME,40), 9), 10)) / RANK(DECAYLINEAR(CORR(RANK(VWAP), RANK(VOLUME), 7),3)))"
        return evaluate_gtja(formula, data)
