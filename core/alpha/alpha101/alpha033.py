import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha033(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha033"

    @property
    def category(self) -> str:
        return "range_rank"

    @property
    def description(self) -> str:
        return "Range rank factor - rolling rank of high-low range over lookback period"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return (data["high"] - data["low"]).rolling(lookback).rank()
