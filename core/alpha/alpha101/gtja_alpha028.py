"""GTJA Alpha28: 3*SMA((CLOSE-TSMIN(LOW,9))/(TSMAX(HIGH,9)-TSMIN(LOW,9))*100,3,1)-2*SMA(SMA((CLOS"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha28(AlphaFactor):
    """GTJA Alpha28: 3*SMA((CLOSE-TSMIN(LOW,9))/(TSMAX(HIGH,9)-TSMIN(LOW,9))*100,3,1)-2*SMA(SMA((CLOS"""

    @property
    def name(self) -> str:
        return "gtja_alpha28"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "3*SMA((CLOSE-TSMIN(LOW,9))/(TSMAX(HIGH,9)-TSMIN(LOW,9))*100,3,1)-2*SMA(SMA((CLOS"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "3*SMA((CLOSE-TSMIN(LOW,9))/(TSMAX(HIGH,9)-TSMIN(LOW,9))*100,3,1)-2*SMA(SMA((CLOSE-TSMIN(LOW,9))/(TSMAX(HIGH,9)-TSMAX(LOW,9))*100,3,1),3,1)"
        return evaluate_gtja(formula, data)
