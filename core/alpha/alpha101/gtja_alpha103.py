"""GTJA Alpha103: SMA(HIGH-LOW,10,2)/SMA(SMA(HIGH-LOW,10,2),10,2)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha103(AlphaFactor):
    """GTJA Alpha103: SMA(HIGH-LOW,10,2)/SMA(SMA(HIGH-LOW,10,2),10,2)"""

    @property
    def name(self) -> str:
        return "gtja_alpha103"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "SMA(HIGH-LOW,10,2)/SMA(SMA(HIGH-LOW,10,2),10,2)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "SMA(HIGH-LOW,10,2)/SMA(SMA(HIGH-LOW,10,2),10,2)"
        return evaluate_gtja(formula, data)
