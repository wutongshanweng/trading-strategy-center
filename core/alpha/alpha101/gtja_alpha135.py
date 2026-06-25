"""GTJA Alpha135: (((-1 * RANK(TSRANK(CLOSE, 10))) * RANK(DELTA(DELTA(CLOSE, 1), 1))) * RANK(TSRAN"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha135(AlphaFactor):
    """GTJA Alpha135: (((-1 * RANK(TSRANK(CLOSE, 10))) * RANK(DELTA(DELTA(CLOSE, 1), 1))) * RANK(TSRAN"""

    @property
    def name(self) -> str:
        return "gtja_alpha135"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(((-1 * RANK(TSRANK(CLOSE, 10))) * RANK(DELTA(DELTA(CLOSE, 1), 1))) * RANK(TSRAN"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(((-1 * RANK(TSRANK(CLOSE, 10))) * RANK(DELTA(DELTA(CLOSE, 1), 1))) * RANK(TSRANK((VOLUME /MEAN(VOLUME,20)), 5)))"
        return evaluate_gtja(formula, data)
