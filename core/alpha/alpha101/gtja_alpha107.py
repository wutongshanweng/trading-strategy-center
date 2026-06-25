"""GTJA Alpha107: (-1 * ((RANK((SUM(DELAY(CLOSE, 5), 20) / 20)) * CORR(CLOSE, VOLUME, 2)) * RANK(C"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha107(AlphaFactor):
    """GTJA Alpha107: (-1 * ((RANK((SUM(DELAY(CLOSE, 5), 20) / 20)) * CORR(CLOSE, VOLUME, 2)) * RANK(C"""

    @property
    def name(self) -> str:
        return "gtja_alpha107"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(-1 * ((RANK((SUM(DELAY(CLOSE, 5), 20) / 20)) * CORR(CLOSE, VOLUME, 2)) * RANK(C"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(-1 * ((RANK((SUM(DELAY(CLOSE, 5), 20) / 20)) * CORR(CLOSE, VOLUME, 2)) * RANK(CORR(SUM(CLOSE, 5), SUM(CLOSE, 20), 2))))"
        return evaluate_gtja(formula, data)
