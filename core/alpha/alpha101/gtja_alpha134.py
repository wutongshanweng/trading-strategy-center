"""GTJA Alpha134: (RANK(CORR(RANK(HIGH), RANK(MEAN(VOLUME,15)), 9))* -1)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha134(AlphaFactor):
    """GTJA Alpha134: (RANK(CORR(RANK(HIGH), RANK(MEAN(VOLUME,15)), 9))* -1)"""

    @property
    def name(self) -> str:
        return "gtja_alpha134"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(RANK(CORR(RANK(HIGH), RANK(MEAN(VOLUME,15)), 9))* -1)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(RANK(CORR(RANK(HIGH), RANK(MEAN(VOLUME,15)), 9))* -1)"
        return evaluate_gtja(formula, data)
