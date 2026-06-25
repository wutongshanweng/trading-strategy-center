"""GTJA Alpha171: MIN(RANK(DECAYLINEAR(((OPEN - TSMIN(OPEN, 12)) / (TSMAX(OPEN, 12) - TSMIN(OPEN, """
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha171(AlphaFactor):
    """GTJA Alpha171: MIN(RANK(DECAYLINEAR(((OPEN - TSMIN(OPEN, 12)) / (TSMAX(OPEN, 12) - TSMIN(OPEN, """

    @property
    def name(self) -> str:
        return "gtja_alpha171"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "MIN(RANK(DECAYLINEAR(((OPEN - TSMIN(OPEN, 12)) / (TSMAX(OPEN, 12) - TSMIN(OPEN, "

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "MIN(RANK(DECAYLINEAR(((OPEN - TSMIN(OPEN, 12)) / (TSMAX(OPEN, 12) - TSMIN(OPEN, 12))), 14)), TSRANK(DECAYLINEAR(((CORR(OPEN, VOLUME, 20) * -1) + OPEN - TSMIN(OPEN,5)), 18), 4))"
        return evaluate_gtja(formula, data)
