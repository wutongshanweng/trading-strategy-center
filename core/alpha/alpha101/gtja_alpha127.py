"""GTJA Alpha127: ((20-HIGHDAY(HIGH,20))/20)*100-((20-LOWDAY(LOW,20))/20)*100"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha127(AlphaFactor):
    """GTJA Alpha127: ((20-HIGHDAY(HIGH,20))/20)*100-((20-LOWDAY(LOW,20))/20)*100"""

    @property
    def name(self) -> str:
        return "gtja_alpha127"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "((20-HIGHDAY(HIGH,20))/20)*100-((20-LOWDAY(LOW,20))/20)*100"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "((20-HIGHDAY(HIGH,20))/20)*100-((20-LOWDAY(LOW,20))/20)*100"
        return evaluate_gtja(formula, data)
