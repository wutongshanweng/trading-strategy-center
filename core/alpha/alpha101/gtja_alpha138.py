"""GTJA Alpha138: (MEAN(VOLUME,9)-MEAN(VOLUME,26))/MEAN(VOLUME,12)*100"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha138(AlphaFactor):
    """GTJA Alpha138: (MEAN(VOLUME,9)-MEAN(VOLUME,26))/MEAN(VOLUME,12)*100"""

    @property
    def name(self) -> str:
        return "gtja_alpha138"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(MEAN(VOLUME,9)-MEAN(VOLUME,26))/MEAN(VOLUME,12)*100"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(MEAN(VOLUME,9)-MEAN(VOLUME,26))/MEAN(VOLUME,12)*100"
        return evaluate_gtja(formula, data)
