"""GTJA Alpha148: ((HIGH-SMA(CLOSE,15,2))-(LOW-SMA(CLOSE,15,2)))/CLOSE"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha148(AlphaFactor):
    """GTJA Alpha148: ((HIGH-SMA(CLOSE,15,2))-(LOW-SMA(CLOSE,15,2)))/CLOSE"""

    @property
    def name(self) -> str:
        return "gtja_alpha148"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "((HIGH-SMA(CLOSE,15,2))-(LOW-SMA(CLOSE,15,2)))/CLOSE"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "((HIGH-SMA(CLOSE,15,2))-(LOW-SMA(CLOSE,15,2)))/CLOSE"
        return evaluate_gtja(formula, data)
