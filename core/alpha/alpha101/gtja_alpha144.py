"""GTJA Alpha144: (((VWAP - MIN(VWAP, 16))) < (CORR(VWAP, MEAN(VOLUME,180), 18)))"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha144(AlphaFactor):
    """GTJA Alpha144: (((VWAP - MIN(VWAP, 16))) < (CORR(VWAP, MEAN(VOLUME,180), 18)))"""

    @property
    def name(self) -> str:
        return "gtja_alpha144"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(((VWAP - MIN(VWAP, 16))) < (CORR(VWAP, MEAN(VOLUME,180), 18)))"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(((VWAP - MIN(VWAP, 16))) < (CORR(VWAP, MEAN(VOLUME,180), 18)))"
        return evaluate_gtja(formula, data)
