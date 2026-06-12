import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha028(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha028"

    @property
    def category(self) -> str:
        return "correlation_rank"

    @property
    def description(self) -> str:
        return "High-low correlation rank factor - rolling rank of high-low correlation over lookback period"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        correlation = data['high'].rolling(lookback).corr(data['low'])
        return correlation.rank()