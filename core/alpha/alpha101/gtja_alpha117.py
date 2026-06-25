"""GTJA Alpha117: (RANK(CORR(SUM(((HIGH + LOW) / 2), 20), SUM(MEAN(VOLUME,60), 20), 9)) < RANK(COR"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha117(AlphaFactor):
    """GTJA Alpha117: (RANK(CORR(SUM(((HIGH + LOW) / 2), 20), SUM(MEAN(VOLUME,60), 20), 9)) < RANK(COR"""

    @property
    def name(self) -> str:
        return "gtja_alpha117"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(RANK(CORR(SUM(((HIGH + LOW) / 2), 20), SUM(MEAN(VOLUME,60), 20), 9)) < RANK(COR"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(RANK(CORR(SUM(((HIGH + LOW) / 2), 20), SUM(MEAN(VOLUME,60), 20), 9)) < RANK(CORR(LOW, VOLUME, 6))) * -1"
        return evaluate_gtja(formula, data)
