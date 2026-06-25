"""GTJA Alpha63: SMA(((HIGH+LOW)/2-(DELAY(HIGH,1)+DELAY(LOW,1))/2)*(HIGH-LOW)/VOLUME,15,2)"""
import pandas as pd
import numpy as np

from .base import AlphaFactor
from .factor_registry import FactorRegistry
from .gtja_evaluator import evaluate_gtja


@FactorRegistry.register
class GTJA_Alpha63(AlphaFactor):
    """GTJA Alpha63: SMA(((HIGH+LOW)/2-(DELAY(HIGH,1)+DELAY(LOW,1))/2)*(HIGH-LOW)/VOLUME,15,2)"""

    @property
    def name(self) -> str:
        return "gtja_alpha63"

    @property
    def category(self) -> str:
        return "gtja"

    @property
    def description(self) -> str:
        return "SMA(((HIGH+LOW)/2-(DELAY(HIGH,1)+DELAY(LOW,1))/2)*(HIGH-LOW)/VOLUME,15,2)"

    def compute(self, data: pd.DataFrame) -> pd.Series:
        formula = "SMA(((HIGH+LOW)/2-(DELAY(HIGH,1)+DELAY(LOW,1))/2)*(HIGH-LOW)/VOLUME,15,2)"
        return evaluate_gtja(formula, data)
