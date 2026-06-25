"""GTJA Alpha75: (VOLUME-DELAY(VOLUME,5))/DELAY(VOLUME,5)*100"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha75(AlphaFactor):
    """GTJA Alpha75: (VOLUME-DELAY(VOLUME,5))/DELAY(VOLUME,5)*100"""

    @property
    def name(self) -> str:
        return "gtja_alpha75"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(VOLUME-DELAY(VOLUME,5))/DELAY(VOLUME,5)*100"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(VOLUME-DELAY(VOLUME,5))/DELAY(VOLUME,5)*100"
        return evaluate_gtja(formula, data)
