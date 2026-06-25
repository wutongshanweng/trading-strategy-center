"""GTJA Alpha79: SUM((CLOSE>DELAY(CLOSE,1)?VOLUME:(CLOSE<DELAY(CLOSE,1)?-VOLUME:0)),20)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha79(AlphaFactor):
    """GTJA Alpha79: SUM((CLOSE>DELAY(CLOSE,1)?VOLUME:(CLOSE<DELAY(CLOSE,1)?-VOLUME:0)),20)"""

    @property
    def name(self) -> str:
        return "gtja_alpha79"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "SUM((CLOSE>DELAY(CLOSE,1)?VOLUME:(CLOSE<DELAY(CLOSE,1)?-VOLUME:0)),20)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "SUM((CLOSE>DELAY(CLOSE,1)?VOLUME:(CLOSE<DELAY(CLOSE,1)?-VOLUME:0)),20)"
        return evaluate_gtja(formula, data)
