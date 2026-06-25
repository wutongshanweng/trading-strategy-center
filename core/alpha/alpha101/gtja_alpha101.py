"""GTJA Alpha101: ((( -1 * RANK((OPEN - DELAY(HIGH, 1)))) * RANK((OPEN - DELAY(CLOSE, 1)))) * RANK"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha101(AlphaFactor):
    """GTJA Alpha101: ((( -1 * RANK((OPEN - DELAY(HIGH, 1)))) * RANK((OPEN - DELAY(CLOSE, 1)))) * RANK"""

    @property
    def name(self) -> str:
        return "gtja_alpha101"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "((( -1 * RANK((OPEN - DELAY(HIGH, 1)))) * RANK((OPEN - DELAY(CLOSE, 1)))) * RANK"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "((( -1 * RANK((OPEN - DELAY(HIGH, 1)))) * RANK((OPEN - DELAY(CLOSE, 1)))) * RANK((OPEN - DELAY(LOW, 1))))"
        return evaluate_gtja(formula, data)
