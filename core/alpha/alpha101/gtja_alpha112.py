"""GTJA Alpha112: SUM(HIGH-OPEN,20)/SUM(OPEN-LOW,20)*100"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha112(AlphaFactor):
    """GTJA Alpha112: SUM(HIGH-OPEN,20)/SUM(OPEN-LOW,20)*100"""

    @property
    def name(self) -> str:
        return "gtja_alpha112"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "SUM(HIGH-OPEN,20)/SUM(OPEN-LOW,20)*100"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "SUM(HIGH-OPEN,20)/SUM(OPEN-LOW,20)*100"
        return evaluate_gtja(formula, data)
