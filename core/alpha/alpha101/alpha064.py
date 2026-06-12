import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha064(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha064"

    @property
    def category(self) -> str:
        return "momentum_rank"

    @property
    def description(self) -> str:
        return "Momentum rank factor - rolling rank of 5-day momentum over lookback period"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return (data["close"] / data["close"].shift(5)).rolling(lookback).rank()
