"""GTJA Alpha119: (RANK(DECAYLINEAR(CORR((VWAP), MEAN(VOLUME,80),17), 20)) / RANK(DECAYLINEAR(DELT"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha119(AlphaFactor):
    """GTJA Alpha119: (RANK(DECAYLINEAR(CORR((VWAP), MEAN(VOLUME,80),17), 20)) / RANK(DECAYLINEAR(DELT"""

    @property
    def name(self) -> str:
        return "gtja_alpha119"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(RANK(DECAYLINEAR(CORR((VWAP), MEAN(VOLUME,80),17), 20)) / RANK(DECAYLINEAR(DELT"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(RANK(DECAYLINEAR(CORR((VWAP), MEAN(VOLUME,80),17), 20)) / RANK(DECAYLINEAR(DELTA(((CLOSE * 0.5) + (VWAP * 0.5)), 3), 16)))"
        return evaluate_gtja(formula, data)
