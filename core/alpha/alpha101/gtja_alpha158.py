"""GTJA Alpha158: (-1*VOLUME/MEAN(VOLUME,20))"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha158(AlphaFactor):
    """GTJA Alpha158: (-1*VOLUME/MEAN(VOLUME,20))"""

    @property
    def name(self) -> str:
        return "gtja_alpha158"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(-1*VOLUME/MEAN(VOLUME,20))"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(-1*VOLUME/MEAN(VOLUME,20))"
        return evaluate_gtja(formula, data)
