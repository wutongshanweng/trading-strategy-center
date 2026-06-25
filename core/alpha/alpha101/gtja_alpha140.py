"""GTJA Alpha140: REGBETA(MEAN(CLOSE,12),SEQUENCE(12))"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha140(AlphaFactor):
    """GTJA Alpha140: REGBETA(MEAN(CLOSE,12),SEQUENCE(12))"""

    @property
    def name(self) -> str:
        return "gtja_alpha140"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "REGBETA(MEAN(CLOSE,12),SEQUENCE(12))"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "REGBETA(MEAN(CLOSE,12),SEQUENCE(12))"
        return evaluate_gtja(formula, data)
