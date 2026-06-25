"""GTJA Alpha143: (MEAN(CLOSE,3)+MEAN(CLOSE,6)+MEAN(CLOSE,12)+MEAN(CLOSE,24))/4"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha143(AlphaFactor):
    """GTJA Alpha143: (MEAN(CLOSE,3)+MEAN(CLOSE,6)+MEAN(CLOSE,12)+MEAN(CLOSE,24))/4"""

    @property
    def name(self) -> str:
        return "gtja_alpha143"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(MEAN(CLOSE,3)+MEAN(CLOSE,6)+MEAN(CLOSE,12)+MEAN(CLOSE,24))/4"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(MEAN(CLOSE,3)+MEAN(CLOSE,6)+MEAN(CLOSE,12)+MEAN(CLOSE,24))/4"
        return evaluate_gtja(formula, data)
