import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha014(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha014"

    @property
    def category(self) -> str:
        return "correlation"

    @property
    def description(self) -> str:
        return "High-low correlation factor - rolling correlation of high and low prices"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return data['high'].rolling(lookback).corr(data['low'])