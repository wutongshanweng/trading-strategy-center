"""GTJA Alpha115: ((RANK((VWAP - MIN(VWAP, 12)))^TSRANK(CORR(TSRANK(VWAP, 20), TSRANK(MEAN(VOLUME,"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha115(AlphaFactor):
    """GTJA Alpha115: ((RANK((VWAP - MIN(VWAP, 12)))^TSRANK(CORR(TSRANK(VWAP, 20), TSRANK(MEAN(VOLUME,"""

    @property
    def name(self) -> str:
        return "gtja_alpha115"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "((RANK((VWAP - MIN(VWAP, 12)))^TSRANK(CORR(TSRANK(VWAP, 20), TSRANK(MEAN(VOLUME,"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "((RANK((VWAP - MIN(VWAP, 12)))^TSRANK(CORR(TSRANK(VWAP, 20), TSRANK(MEAN(VOLUME,60), 2), 18), 3)) * -1)"
        return evaluate_gtja(formula, data)
