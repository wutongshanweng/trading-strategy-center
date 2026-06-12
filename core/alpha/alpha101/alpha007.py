import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha007(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha007"

    @property
    def category(self) -> str:
        return "correlation"

    @property
    def description(self) -> str:
        return "Price-volume correlation factor - rolling correlation between close and volume"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return data['close'].rolling(lookback).corr(data['volume'])