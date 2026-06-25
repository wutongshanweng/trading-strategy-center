"""GTJA Alpha68: ((TSRANK(DECAYLINEAR(DECAYLINEAR(CORR((CLOSE), VOLUME, 10), 16), 4), 5) - RANK(D"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha68(AlphaFactor):
    """GTJA Alpha68: ((TSRANK(DECAYLINEAR(DECAYLINEAR(CORR((CLOSE), VOLUME, 10), 16), 4), 5) - RANK(D"""

    @property
    def name(self) -> str:
        return "gtja_alpha68"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "((TSRANK(DECAYLINEAR(DECAYLINEAR(CORR((CLOSE), VOLUME, 10), 16), 4), 5) - RANK(D"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "((TSRANK(DECAYLINEAR(DECAYLINEAR(CORR((CLOSE), VOLUME, 10), 16), 4), 5) - RANK(DECAYLINEAR(CORR(VWAP, MEAN(VOLUME,30), 4),3))) * -1)"
        return evaluate_gtja(formula, data)
