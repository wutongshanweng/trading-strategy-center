"""GTJA Alpha47: SMA((TSMAX(HIGH,6)-CLOSE)/(TSMAX(HIGH,6)-TSMIN(LOW,6))*100,9,1)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha47(AlphaFactor):
    """GTJA Alpha47: SMA((TSMAX(HIGH,6)-CLOSE)/(TSMAX(HIGH,6)-TSMIN(LOW,6))*100,9,1)"""

    @property
    def name(self) -> str:
        return "gtja_alpha47"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "SMA((TSMAX(HIGH,6)-CLOSE)/(TSMAX(HIGH,6)-TSMIN(LOW,6))*100,9,1)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "SMA((TSMAX(HIGH,6)-CLOSE)/(TSMAX(HIGH,6)-TSMIN(LOW,6))*100,9,1)"
        return evaluate_gtja(formula, data)
