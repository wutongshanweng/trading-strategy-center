"""GTJA Alpha160: ((((RANK((1 / CLOSE)) * VOLUME) / MEAN(VOLUME,20)) * ((HIGH * RANK((HIGH - CLOSE"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha160(AlphaFactor):
    """GTJA Alpha160: ((((RANK((1 / CLOSE)) * VOLUME) / MEAN(VOLUME,20)) * ((HIGH * RANK((HIGH - CLOSE"""

    @property
    def name(self) -> str:
        return "gtja_alpha160"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "((((RANK((1 / CLOSE)) * VOLUME) / MEAN(VOLUME,20)) * ((HIGH * RANK((HIGH - CLOSE"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "((((RANK((1 / CLOSE)) * VOLUME) / MEAN(VOLUME,20)) * ((HIGH * RANK((HIGH - CLOSE))) / (SUM(HIGH, 5) / 5))) - RANK((VWAP - DELAY(VWAP, 5))))"
        return evaluate_gtja(formula, data)
