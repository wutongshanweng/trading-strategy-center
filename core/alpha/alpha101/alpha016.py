import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha016(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha016"

    @property
    def category(self) -> str:
        return "rank"

    @property
    def description(self) -> str:
        return "Price rank factor - rolling rank of close price over lookback period"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return data['close'].rolling(lookback).rank()