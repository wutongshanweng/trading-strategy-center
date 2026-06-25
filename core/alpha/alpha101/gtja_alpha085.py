"""GTJA Alpha85: ( RANK(CORR(RANK(VWAP), RANK(VOLUME), 5)) * -1)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha85(AlphaFactor):
    """GTJA Alpha85: ( RANK(CORR(RANK(VWAP), RANK(VOLUME), 5)) * -1)"""

    @property
    def name(self) -> str:
        return "gtja_alpha85"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "( RANK(CORR(RANK(VWAP), RANK(VOLUME), 5)) * -1)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "( RANK(CORR(RANK(VWAP), RANK(VOLUME), 5)) * -1)"
        return evaluate_gtja(formula, data)
