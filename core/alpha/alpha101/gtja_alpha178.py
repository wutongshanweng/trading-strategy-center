"""GTJA Alpha178: (RANK(DECAYLINEAR(DELTA(VWAP, 4), 7)) + TSRANK(DECAYLINEAR((((LOW * 0.9) + (LOW """
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha178(AlphaFactor):
    """GTJA Alpha178: (RANK(DECAYLINEAR(DELTA(VWAP, 4), 7)) + TSRANK(DECAYLINEAR((((LOW * 0.9) + (LOW """

    @property
    def name(self) -> str:
        return "gtja_alpha178"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(RANK(DECAYLINEAR(DELTA(VWAP, 4), 7)) + TSRANK(DECAYLINEAR((((LOW * 0.9) + (LOW "

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(RANK(DECAYLINEAR(DELTA(VWAP, 4), 7)) + TSRANK(DECAYLINEAR((((LOW * 0.9) + (LOW * 0.1)) - VWAP) / (OPEN - ((HIGH + LOW) / 2)), 11), 7)) * -1"
        return evaluate_gtja(formula, data)
