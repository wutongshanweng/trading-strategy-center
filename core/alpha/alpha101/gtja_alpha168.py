"""GTJA Alpha168: (CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1)*VOLUME"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha168(AlphaFactor):
    """GTJA Alpha168: (CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1)*VOLUME"""

    @property
    def name(self) -> str:
        return "gtja_alpha168"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1)*VOLUME"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1)*VOLUME"
        return evaluate_gtja(formula, data)
