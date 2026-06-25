"""GTJA Alpha161: (( -1 * ((LOW - CLOSE) * (OPEN^5))) / ((CLOSE - HIGH) * (CLOSE^5)))"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha161(AlphaFactor):
    """GTJA Alpha161: (( -1 * ((LOW - CLOSE) * (OPEN^5))) / ((CLOSE - HIGH) * (CLOSE^5)))"""

    @property
    def name(self) -> str:
        return "gtja_alpha161"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(( -1 * ((LOW - CLOSE) * (OPEN^5))) / ((CLOSE - HIGH) * (CLOSE^5)))"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(( -1 * ((LOW - CLOSE) * (OPEN^5))) / ((CLOSE - HIGH) * (CLOSE^5)))"
        return evaluate_gtja(formula, data)
