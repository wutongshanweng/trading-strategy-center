"""GTJA Alpha104: SUM(MAX(0,HIGH-DELAY(CLOSE,1)),20)/SUM(MAX(0,DELAY(CLOSE,1)-LOW),20)*100"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha104(AlphaFactor):
    """GTJA Alpha104: SUM(MAX(0,HIGH-DELAY(CLOSE,1)),20)/SUM(MAX(0,DELAY(CLOSE,1)-LOW),20)*100"""

    @property
    def name(self) -> str:
        return "gtja_alpha104"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "SUM(MAX(0,HIGH-DELAY(CLOSE,1)),20)/SUM(MAX(0,DELAY(CLOSE,1)-LOW),20)*100"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "SUM(MAX(0,HIGH-DELAY(CLOSE,1)),20)/SUM(MAX(0,DELAY(CLOSE,1)-LOW),20)*100"
        return evaluate_gtja(formula, data)
