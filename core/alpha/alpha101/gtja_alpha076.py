"""GTJA Alpha76: SMA(VOLUME,21,2)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha76(AlphaFactor):
    """GTJA Alpha76: SMA(VOLUME,21,2)"""

    @property
    def name(self) -> str:
        return "gtja_alpha76"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "SMA(VOLUME,21,2)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "SMA(VOLUME,21,2)"
        return evaluate_gtja(formula, data)
