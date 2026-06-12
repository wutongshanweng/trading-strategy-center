import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha027(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha027"

    @property
    def category(self) -> str:
        return "acceleration_rank"

    @property
    def description(self) -> str:
        return "Acceleration rank factor - rolling rank of acceleration over lookback period"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        acceleration = data['close'].pct_change().diff()
        return acceleration.rolling(lookback).rank()