"""GTJA Alpha136: CLOSE>DELAY(CLOSE,1)?(CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1)*SELF:SELF"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha136(AlphaFactor):
    """GTJA Alpha136: CLOSE>DELAY(CLOSE,1)?(CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1)*SELF:SELF"""

    @property
    def name(self) -> str:
        return "gtja_alpha136"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "CLOSE>DELAY(CLOSE,1)?(CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1)*SELF:SELF"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "CLOSE>DELAY(CLOSE,1)?(CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1)*SELF:SELF"
        return evaluate_gtja(formula, data)
