"""GTJA Alpha80: (TSRANK((VOLUME / MEAN(VOLUME,20)), 20) * TSRANK((-1 * DELTA(CLOSE, 7)), 8))"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha80(AlphaFactor):
    """GTJA Alpha80: (TSRANK((VOLUME / MEAN(VOLUME,20)), 20) * TSRANK((-1 * DELTA(CLOSE, 7)), 8))"""

    @property
    def name(self) -> str:
        return "gtja_alpha80"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(TSRANK((VOLUME / MEAN(VOLUME,20)), 20) * TSRANK((-1 * DELTA(CLOSE, 7)), 8))"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(TSRANK((VOLUME / MEAN(VOLUME,20)), 20) * TSRANK((-1 * DELTA(CLOSE, 7)), 8))"
        return evaluate_gtja(formula, data)
