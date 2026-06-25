"""GTJA Alpha77: SMA((TSMAX(HIGH,6)-CLOSE)/(TSMAX(HIGH,6)-TSMIN(LOW,6))*100,20,1)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha77(AlphaFactor):
    """GTJA Alpha77: SMA((TSMAX(HIGH,6)-CLOSE)/(TSMAX(HIGH,6)-TSMIN(LOW,6))*100,20,1)"""

    @property
    def name(self) -> str:
        return "gtja_alpha77"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "SMA((TSMAX(HIGH,6)-CLOSE)/(TSMAX(HIGH,6)-TSMIN(LOW,6))*100,20,1)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "SMA((TSMAX(HIGH,6)-CLOSE)/(TSMAX(HIGH,6)-TSMIN(LOW,6))*100,20,1)"
        return evaluate_gtja(formula, data)
