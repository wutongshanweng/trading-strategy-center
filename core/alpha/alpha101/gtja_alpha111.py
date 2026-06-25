"""GTJA Alpha111: ((TSRANK(VOLUME, 32) * (1 - TSRANK(((CLOSE + HIGH) - LOW), 16))) * (1 - TSRANK(R"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha111(AlphaFactor):
    """GTJA Alpha111: ((TSRANK(VOLUME, 32) * (1 - TSRANK(((CLOSE + HIGH) - LOW), 16))) * (1 - TSRANK(R"""

    @property
    def name(self) -> str:
        return "gtja_alpha111"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "((TSRANK(VOLUME, 32) * (1 - TSRANK(((CLOSE + HIGH) - LOW), 16))) * (1 - TSRANK(R"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "((TSRANK(VOLUME, 32) * (1 - TSRANK(((CLOSE + HIGH) - LOW), 16))) * (1 - TSRANK(RET, 32)))"
        return evaluate_gtja(formula, data)
