import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha048(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha048"

    @property
    def category(self) -> str:
        return "volume_price_rank"

    @property
    def description(self) -> str:
        return "Volume price rank factor - rolling rank of close*volume over lookback period"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return (data["close"] * data["volume"]).rolling(lookback).rank()
