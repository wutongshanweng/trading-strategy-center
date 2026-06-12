import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha081(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha081"

    @property
    def category(self) -> str:
        return "volume_momentum_rank"

    @property
    def description(self) -> str:
        return "Volume momentum rank factor - rolling rank of 5-day volume momentum over lookback period"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return (data["volume"] / data["volume"].shift(5)).rolling(lookback).rank()
