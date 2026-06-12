import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha009(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha009"

    @property
    def category(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Momentum factor - close relative to previous close (5-day shift)"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return data['close'] / data['close'].shift(5)