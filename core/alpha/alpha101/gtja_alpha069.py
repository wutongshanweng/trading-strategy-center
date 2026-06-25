"""GTJA Alpha69: (RANK(CORR(SUM(((LOW * 0.35) + (VWAP * 0.65)), 20), SUM(MEAN(VOLUME,40), 20), 7)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha69(AlphaFactor):
    """GTJA Alpha69: (RANK(CORR(SUM(((LOW * 0.35) + (VWAP * 0.65)), 20), SUM(MEAN(VOLUME,40), 20), 7)"""

    @property
    def name(self) -> str:
        return "gtja_alpha69"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "(RANK(CORR(SUM(((LOW * 0.35) + (VWAP * 0.65)), 20), SUM(MEAN(VOLUME,40), 20), 7)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "(RANK(CORR(SUM(((LOW * 0.35) + (VWAP * 0.65)), 20), SUM(MEAN(VOLUME,40), 20), 7)) + RANK(CORR(RANK(VWAP), RANK(VOLUME), 6)))"
        return evaluate_gtja(formula, data)
