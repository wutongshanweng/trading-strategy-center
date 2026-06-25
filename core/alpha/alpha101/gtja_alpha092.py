"""GTJA Alpha92: STD(VOLUME,10)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha92(AlphaFactor):
    """GTJA Alpha92: STD(VOLUME,10)"""

    @property
    def name(self) -> str:
        return "gtja_alpha92"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "STD(VOLUME,10)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "STD(VOLUME,10)"
        return evaluate_gtja(formula, data)
