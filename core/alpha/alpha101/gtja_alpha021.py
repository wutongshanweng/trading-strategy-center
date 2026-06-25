"""GTJA Alpha21: REGBETA(MEAN(CLOSE,6),SEQUENCE(6))"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha21(AlphaFactor):
    """GTJA Alpha21: REGBETA(MEAN(CLOSE,6),SEQUENCE(6))"""

    @property
    def name(self) -> str:
        return "gtja_alpha21"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "REGBETA(MEAN(CLOSE,6),SEQUENCE(6))"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "REGBETA(MEAN(CLOSE,6),SEQUENCE(6))"
        return evaluate_gtja(formula, data)
