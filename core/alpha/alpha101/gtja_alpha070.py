"""GTJA Alpha70: COUNT(CLOSE>OPEN & BANCHMARKINDEXCLOSE<BANCHMARKINDEXOPEN,50)/COUNT(BANCHMARKIND"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha70(AlphaFactor):
    """GTJA Alpha70: COUNT(CLOSE>OPEN & BANCHMARKINDEXCLOSE<BANCHMARKINDEXOPEN,50)/COUNT(BANCHMARKIND"""

    @property
    def name(self) -> str:
        return "gtja_alpha70"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "COUNT(CLOSE>OPEN & BANCHMARKINDEXCLOSE<BANCHMARKINDEXOPEN,50)/COUNT(BANCHMARKIND"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "COUNT(CLOSE>OPEN & BANCHMARKINDEXCLOSE<BANCHMARKINDEXOPEN,50)/COUNT(BANCHMARKINDEXCLOSE<BANCHMARKINDEXOPEN,50)"
        return evaluate_gtja(formula, data)
