import pandas as pd

from .base import AlphaFactor
from .factor_registry import FactorRegistry


@FactorRegistry.register
class Alpha005(AlphaFactor):
    @property
    def name(self) -> str:
        return "alpha005"

    @property
    def category(self) -> str:
        return "range"

    @property
    def description(self) -> str:
        return "Range factor - high-low range relative to close price"

    def compute(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        return (data['high'] - data['low']) / data['close']