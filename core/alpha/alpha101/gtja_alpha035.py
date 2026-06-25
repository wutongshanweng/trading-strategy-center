"""GTJA Alpha35: (MIN(RANK(DECAYLINEAR(DELTA(OPEN, 1), 15)), RANK(DECAYLINEAR(CORR((VOLUME), ((OP"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha35(AlphaFactor):
    """GTJA Alpha35: (MIN(RANK(DECAYLINEAR(DELTA(OPEN, 1), 15)), RANK(DECAYLINEAR(CORR((VOLUME), ((OP"""

    @property
    def name(self) -> str:
        return "gtja_alpha35"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(MIN(RANK(DECAYLINEAR(DELTA(OPEN, 1), 15)), RANK(DECAYLINEAR(CORR((VOLUME), ((OP"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(MIN(RANK(DECAYLINEAR(DELTA(OPEN, 1), 15)), RANK(DECAYLINEAR(CORR((VOLUME), ((OPEN * 0.65) + (OPEN *0.35)), 17),7))) * -1)"
        return evaluate_gtja(formula, data)
