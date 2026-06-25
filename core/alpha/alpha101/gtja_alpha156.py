"""GTJA Alpha156: -20*((20-1)^1.5)*SUM(CLOSE/DELAY(CLOSE,1)-1-MEAN(CLOSE/DELAY(CLOSE,1)-1,20),20)/"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha156(AlphaFactor):
    """GTJA Alpha156: -20*((20-1)^1.5)*SUM(CLOSE/DELAY(CLOSE,1)-1-MEAN(CLOSE/DELAY(CLOSE,1)-1,20),20)/"""

    @property
    def name(self) -> str:
        return "gtja_alpha156"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "-20*((20-1)^1.5)*SUM(CLOSE/DELAY(CLOSE,1)-1-MEAN(CLOSE/DELAY(CLOSE,1)-1,20),20)/"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "-20*((20-1)^1.5)*SUM(CLOSE/DELAY(CLOSE,1)-1-MEAN(CLOSE/DELAY(CLOSE,1)-1,20),20)/((20-1)*(20-2)*((SUM((CLOSE/DELAY(CLOSE,1),20)^2,20))^1.5))"
        return evaluate_gtja(formula, data)
