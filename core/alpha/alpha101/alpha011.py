import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha011(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha011"

    @property
    def category(self) -> str:
        return "correlation_momentum"

    @property
    def description(self) -> str:
        return "Correlation momentum factor - rolling correlation of close with shifted close"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        close = data['close']
        shifted_close = close.shift(1)
        return close.rolling(lookback).corr(shifted_close)