"""GTJA Alpha172: RANK(DECAYLINEAR(CORR(((HIGH + LOW) / 2), MEAN(MEAN(VOLUME,40), 20), 4), 15)) / """
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha172(AlphaFactor):
    """GTJA Alpha172: RANK(DECAYLINEAR(CORR(((HIGH + LOW) / 2), MEAN(MEAN(VOLUME,40), 20), 4), 15)) / """

    @property
    def name(self) -> str:
        return "gtja_alpha172"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "RANK(DECAYLINEAR(CORR(((HIGH + LOW) / 2), MEAN(MEAN(VOLUME,40), 20), 4), 15)) / "

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "RANK(DECAYLINEAR(CORR(((HIGH + LOW) / 2), MEAN(MEAN(VOLUME,40), 20), 4), 15)) / RANK(DECAYLINEAR(DELTA(((CLOSE * 0.5) + (VWAP * 0.5)), 2), 16))"
        return evaluate_gtja(formula, data)
