"""GTJA Alpha39: ((RANK(DECAYLINEAR(DELTA((CLOSE), 2),8)) - RANK(DECAYLINEAR(CORR(((VWAP * 0.3) +"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha39(AlphaFactor):
    """GTJA Alpha39: ((RANK(DECAYLINEAR(DELTA((CLOSE), 2),8)) - RANK(DECAYLINEAR(CORR(((VWAP * 0.3) +"""

    @property
    def name(self) -> str:
        return "gtja_alpha39"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "((RANK(DECAYLINEAR(DELTA((CLOSE), 2),8)) - RANK(DECAYLINEAR(CORR(((VWAP * 0.3) +"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "((RANK(DECAYLINEAR(DELTA((CLOSE), 2),8)) - RANK(DECAYLINEAR(CORR(((VWAP * 0.3) + (OPEN * 0.7)), SUM(MEAN(VOLUME,180), 37), 14), 12))) * -1)"
        return evaluate_gtja(formula, data)
