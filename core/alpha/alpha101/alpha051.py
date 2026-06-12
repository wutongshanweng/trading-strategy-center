import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha051(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha051"

    @property
    def category(self) -> str:
        return "high_rank"

    @property
    def description(self) -> str:
        return "High rank factor - rolling rank of high prices over lookback period"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return data["high"].rolling(lookback).rank()
