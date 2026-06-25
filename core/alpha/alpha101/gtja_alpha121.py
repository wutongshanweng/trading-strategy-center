"""GTJA Alpha121: (MEAN((100*(CLOSE-MAX(CLOSE,12))/(MAX(CLOSE,12)))^2))^(1/2)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha121(AlphaFactor):
    """GTJA Alpha121: (MEAN((100*(CLOSE-MAX(CLOSE,12))/(MAX(CLOSE,12)))^2))^(1/2)"""

    @property
    def name(self) -> str:
        return "gtja_alpha121"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(MEAN((100*(CLOSE-MAX(CLOSE,12))/(MAX(CLOSE,12)))^2))^(1/2)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(MEAN((100*(CLOSE-MAX(CLOSE,12))/(MAX(CLOSE,12)))^2))^(1/2)"
        return evaluate_gtja(formula, data)
