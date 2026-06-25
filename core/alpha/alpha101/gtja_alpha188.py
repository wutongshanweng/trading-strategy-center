"""GTJA Alpha188: ((HIGH-LOW-SMA(HIGH-LOW,11,2))/SMA(HIGH-LOW,11,2))*100"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha188(AlphaFactor):
    """GTJA Alpha188: ((HIGH-LOW-SMA(HIGH-LOW,11,2))/SMA(HIGH-LOW,11,2))*100"""

    @property
    def name(self) -> str:
        return "gtja_alpha188"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "((HIGH-LOW-SMA(HIGH-LOW,11,2))/SMA(HIGH-LOW,11,2))*100"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "((HIGH-LOW-SMA(HIGH-LOW,11,2))/SMA(HIGH-LOW,11,2))*100"
        return evaluate_gtja(formula, data)
