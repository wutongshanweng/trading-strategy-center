import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha052(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha052"

    @property
    def category(self) -> str:
        return "low_rank"

    @property
    def description(self) -> str:
        return "Low rank factor - rolling rank of low prices over lookback period"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return data["low"].rolling(lookback).rank()
