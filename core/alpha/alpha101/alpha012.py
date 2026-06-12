import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha012(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha012"

    @property
    def category(self) -> str:
        return "volume_change"

    @property
    def description(self) -> str:
        return "Volume change factor - percentage change in volume over 5 periods"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return data['volume'].pct_change(5)