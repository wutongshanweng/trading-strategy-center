"""GTJA Alpha97: ((20-LOWDAY(LOW,20))/20)*100"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha97(AlphaFactor):
    """GTJA Alpha97: ((20-LOWDAY(LOW,20))/20)*100"""

    @property
    def name(self) -> str:
        return "gtja_alpha97"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "((20-LOWDAY(LOW,20))/20)*100"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "((20-LOWDAY(LOW,20))/20)*100"
        return evaluate_gtja(formula, data)
