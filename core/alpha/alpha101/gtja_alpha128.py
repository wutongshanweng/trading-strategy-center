"""GTJA Alpha128: (CLOSE-DELAY(CLOSE,12))/DELAY(CLOSE,12)*VOLUME"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha128(AlphaFactor):
    """GTJA Alpha128: (CLOSE-DELAY(CLOSE,12))/DELAY(CLOSE,12)*VOLUME"""

    @property
    def name(self) -> str:
        return "gtja_alpha128"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(CLOSE-DELAY(CLOSE,12))/DELAY(CLOSE,12)*VOLUME"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(CLOSE-DELAY(CLOSE,12))/DELAY(CLOSE,12)*VOLUME"
        return evaluate_gtja(formula, data)
