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

    def compute(self, data: pd.DataFrame) -> pd.Series:
        return (data['high'] - data['low']) / data['close']