"""GTJA Alpha44: (TSRANK(DECAYLINEAR(CORR(((LOW )), MEAN(VOLUME,10), 7), 6),4) + TSRANK(DECAYLINE"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha44(AlphaFactor):
    """GTJA Alpha44: (TSRANK(DECAYLINEAR(CORR(((LOW )), MEAN(VOLUME,10), 7), 6),4) + TSRANK(DECAYLINE"""

    @property
    def name(self) -> str:
        return "gtja_alpha44"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(TSRANK(DECAYLINEAR(CORR(((LOW )), MEAN(VOLUME,10), 7), 6),4) + TSRANK(DECAYLINE"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(TSRANK(DECAYLINEAR(CORR(((LOW )), MEAN(VOLUME,10), 7), 6),4) + TSRANK(DECAYLINEAR(DELTA((VWAP), 3), 10), 15))"
        return evaluate_gtja(formula, data)
