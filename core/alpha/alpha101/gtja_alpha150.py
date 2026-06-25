"""GTJA Alpha150: SMA((CLOSE<=DELAY(CLOSE,1)?STD(CLOSE,20):0),20,1)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha150(AlphaFactor):
    """GTJA Alpha150: SMA((CLOSE<=DELAY(CLOSE,1)?STD(CLOSE,20):0),20,1)"""

    @property
    def name(self) -> str:
        return "gtja_alpha150"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "SMA((CLOSE<=DELAY(CLOSE,1)?STD(CLOSE,20):0),20,1)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "SMA((CLOSE<=DELAY(CLOSE,1)?STD(CLOSE,20):0),20,1)"
        return evaluate_gtja(formula, data)
