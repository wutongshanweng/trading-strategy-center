"""GTJA Alpha65: STD(AMOUNT,6)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha65(AlphaFactor):
    """GTJA Alpha65: STD(AMOUNT,6)"""

    @property
    def name(self) -> str:
        return "gtja_alpha65"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "STD(AMOUNT,6)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "STD(AMOUNT,6)"
        return evaluate_gtja(formula, data)
