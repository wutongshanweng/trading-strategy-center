"""GTJA Alpha166: CORR(RANK(((CLOSE - TSMIN(LOW, 12)) / (TSMAX(HIGH, 12) - TSMIN(LOW,12)))), RANK("""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha166(AlphaFactor):
    """GTJA Alpha166: CORR(RANK(((CLOSE - TSMIN(LOW, 12)) / (TSMAX(HIGH, 12) - TSMIN(LOW,12)))), RANK("""

    @property
    def name(self) -> str:
        return "gtja_alpha166"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "CORR(RANK(((CLOSE - TSMIN(LOW, 12)) / (TSMAX(HIGH, 12) - TSMIN(LOW,12)))), RANK("

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "CORR(RANK(((CLOSE - TSMIN(LOW, 12)) / (TSMAX(HIGH, 12) - TSMIN(LOW,12)))), RANK(VOLUME), 6)"
        return evaluate_gtja(formula, data)
