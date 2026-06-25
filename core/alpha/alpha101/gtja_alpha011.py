"""GTJA Alpha11: SUM(((CLOSE-LOW)-(HIGH-CLOSE))./(HIGH-LOW).*VOLUME,6)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha11(AlphaFactor):
    """GTJA Alpha11: SUM(((CLOSE-LOW)-(HIGH-CLOSE))./(HIGH-LOW).*VOLUME,6)"""

    @property
    def name(self) -> str:
        return "gtja_alpha11"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "SUM(((CLOSE-LOW)-(HIGH-CLOSE))./(HIGH-LOW).*VOLUME,6)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "SUM(((CLOSE-LOW)-(HIGH-CLOSE))./(HIGH-LOW).*VOLUME,6)"
        return evaluate_gtja(formula, data)
