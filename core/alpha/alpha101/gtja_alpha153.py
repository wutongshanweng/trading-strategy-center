"""GTJA Alpha153: RANK(((((-1 * RET) * MEAN(VOLUME,20)) * VWAP) * (HIGH - CLOSE)))"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha153(AlphaFactor):
    """GTJA Alpha153: RANK(((((-1 * RET) * MEAN(VOLUME,20)) * VWAP) * (HIGH - CLOSE)))"""

    @property
    def name(self) -> str:
        return "gtja_alpha153"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "RANK(((((-1 * RET) * MEAN(VOLUME,20)) * VWAP) * (HIGH - CLOSE)))"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "RANK(((((-1 * RET) * MEAN(VOLUME,20)) * VWAP) * (HIGH - CLOSE)))"
        return evaluate_gtja(formula, data)
