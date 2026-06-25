"""GTJA Alpha174: (MAX(RANK(DECAYLINEAR(DELTA(VWAP, 1), 12)), RANK(DECAYLINEAR(RANK(CORR((LOW),MEA"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha174(AlphaFactor):
    """GTJA Alpha174: (MAX(RANK(DECAYLINEAR(DELTA(VWAP, 1), 12)), RANK(DECAYLINEAR(RANK(CORR((LOW),MEA"""

    @property
    def name(self) -> str:
        return "gtja_alpha174"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(MAX(RANK(DECAYLINEAR(DELTA(VWAP, 1), 12)), RANK(DECAYLINEAR(RANK(CORR((LOW),MEA"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(MAX(RANK(DECAYLINEAR(DELTA(VWAP, 1), 12)), RANK(DECAYLINEAR(RANK(CORR((LOW),MEAN(VOLUME,80), 8)), 17))) * -1)"
        return evaluate_gtja(formula, data)
