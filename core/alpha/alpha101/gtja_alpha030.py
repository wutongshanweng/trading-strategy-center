"""GTJA Alpha30: WMA((REGRESI(CLOSE/DELAY(CLOSE)-1,MKT,SMB,HML,60))^2,20)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha30(AlphaFactor):
    """GTJA Alpha30: WMA((REGRESI(CLOSE/DELAY(CLOSE)-1,MKT,SMB,HML,60))^2,20)"""

    @property
    def name(self) -> str:
        return "gtja_alpha30"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "WMA((REGRESI(CLOSE/DELAY(CLOSE)-1,MKT,SMB,HML,60))^2,20)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "WMA((REGRESI(CLOSE/DELAY(CLOSE)-1,MKT,SMB,HML,60))^2,20)"
        return evaluate_gtja(formula, data)
