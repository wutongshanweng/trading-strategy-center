"""GTJA Alpha170: MAX(RANK(DECAYLINEAR(DELTA(((CLOSE * 0.5) + (VWAP * 0.5)), 2), 3)), TSRANK(DECAY"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha170(AlphaFactor):
    """GTJA Alpha170: MAX(RANK(DECAYLINEAR(DELTA(((CLOSE * 0.5) + (VWAP * 0.5)), 2), 3)), TSRANK(DECAY"""

    @property
    def name(self) -> str:
        return "gtja_alpha170"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "MAX(RANK(DECAYLINEAR(DELTA(((CLOSE * 0.5) + (VWAP * 0.5)), 2), 3)), TSRANK(DECAY"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "MAX(RANK(DECAYLINEAR(DELTA(((CLOSE * 0.5) + (VWAP * 0.5)), 2), 3)), TSRANK(DECAYLINEAR(ABS(CORR(CLOSE, MEAN(VOLUME,30), 13)), 5), 15))"
        return evaluate_gtja(formula, data)
