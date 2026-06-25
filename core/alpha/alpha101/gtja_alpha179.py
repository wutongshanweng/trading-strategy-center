"""GTJA Alpha179: ((RANK(DECAYLINEAR(DELTA(((LOW * 0.7) + (VWAP *0.3)), 3), 20)) - TSRANK(DECAYLIN"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha179(AlphaFactor):
    """GTJA Alpha179: ((RANK(DECAYLINEAR(DELTA(((LOW * 0.7) + (VWAP *0.3)), 3), 20)) - TSRANK(DECAYLIN"""

    @property
    def name(self) -> str:
        return "gtja_alpha179"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "((RANK(DECAYLINEAR(DELTA(((LOW * 0.7) + (VWAP *0.3)), 3), 20)) - TSRANK(DECAYLIN"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "((RANK(DECAYLINEAR(DELTA(((LOW * 0.7) + (VWAP *0.3)), 3), 20)) - TSRANK(DECAYLINEAR(TSRANK(CORR(TSRANK(LOW, 8), TSRANK(MEAN(VOLUME,60), 17), 5), 19), 16), 7)) * -1)"
        return evaluate_gtja(formula, data)
