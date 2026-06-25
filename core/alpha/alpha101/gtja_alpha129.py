"""GTJA Alpha129: SMA(DELAY(CLOSE/DELAY(CLOSE,20),1),20,1)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha129(AlphaFactor):
    """GTJA Alpha129: SMA(DELAY(CLOSE/DELAY(CLOSE,20),1),20,1)"""

    @property
    def name(self) -> str:
        return "gtja_alpha129"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "SMA(DELAY(CLOSE/DELAY(CLOSE,20),1),20,1)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "SMA(DELAY(CLOSE/DELAY(CLOSE,20),1),20,1)"
        return evaluate_gtja(formula, data)
