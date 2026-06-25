"""GTJA Alpha10: (RANK(MAX(((RET < 0) ? STD(RET, 20) : CLOSE)^2),5))"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha10(AlphaFactor):
    """GTJA Alpha10: (RANK(MAX(((RET < 0) ? STD(RET, 20) : CLOSE)^2),5))"""

    @property
    def name(self) -> str:
        return "gtja_alpha10"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(RANK(MAX(((RET < 0) ? STD(RET, 20) : CLOSE)^2),5))"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(RANK(MAX(((RET < 0) ? STD(RET, 20) : CLOSE)^2),5))"
        return evaluate_gtja(formula, data)
