"""GTJA Alpha1: (-1 * CORR(RANK(DELTA(LOG(VOLUME), 1)), RANK(((CLOSE - OPEN) / OPEN)), 6))"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha1(AlphaFactor):
    """GTJA Alpha1: (-1 * CORR(RANK(DELTA(LOG(VOLUME), 1)), RANK(((CLOSE - OPEN) / OPEN)), 6))"""

    @property
    def name(self) -> str:
        return "gtja_alpha1"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(-1 * CORR(RANK(DELTA(LOG(VOLUME), 1)), RANK(((CLOSE - OPEN) / OPEN)), 6))"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(-1 * CORR(RANK(DELTA(LOG(VOLUME), 1)), RANK(((CLOSE - OPEN) / OPEN)), 6))"
        return evaluate_gtja(formula, data)
