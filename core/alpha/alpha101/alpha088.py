import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha088(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha088"

    @property
    def category(self) -> str:
        return "volume_rank"

    @property
    def description(self) -> str:
        return "Volume rank factor - rolling rank of volume over lookback period"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return data["volume"].rolling(lookback).rank()
